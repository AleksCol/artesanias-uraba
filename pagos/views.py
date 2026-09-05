"""Cobro con Stripe Checkout.

Dos reglas que ordenan todo este archivo:

1. Los datos de la tarjeta nunca pasan por acá. Se redirige a Stripe y se
   vuelve; el servidor propio no ve un número de tarjeta jamás.
2. El pago se da por confirmado en el webhook, no cuando el navegador
   regresa. La vuelta del navegador solo dice que alguien volvió: se puede
   falsificar escribiendo la URL, y se pierde si cierran la pestaña.
"""

import stripe
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Greatest
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from catalogo.models import Producto
from pedidos.carrito import Carrito
from pedidos.models import ItemPedido, Pedido

from .forms import DatosDeEnvioForm

class SinExistencias(Exception):
    """Se vendió el inventario entre que se armó el carrito y se fue a pagar."""


@transaction.atomic
def _crear_pedido(carrito: Carrito, datos: dict) -> Pedido:
    lineas = list(carrito)
    if not lineas:
        raise SinExistencias("El carrito está vacío.")

    # Se bloquean las filas de producto para que dos compras a la vez no
    # vendan la misma última pieza.
    productos = Producto.objects.select_for_update().in_bulk(
        [linea.producto.pk for linea in lineas]
    )

    total = 0
    items: list[ItemPedido] = []
    for linea in lineas:
        producto = productos.get(linea.producto.pk)
        if producto is None or producto.stock < linea.cantidad:
            disponibles = 0 if producto is None else producto.stock
            raise SinExistencias(
                f"Quedan {disponibles} de {linea.producto.nombre} y pediste "
                f"{linea.cantidad}. Ajusta el carrito y volvemos a intentar."
            )
        total += producto.precio * linea.cantidad
        items.append(
            ItemPedido(
                producto=producto,
                cantidad=linea.cantidad,
                precio_unitario=producto.precio,
            )
        )

    pedido = Pedido.objects.create(
        email=datos["email"],
        direccion_de_envio=datos["direccion_de_envio"],
        total=total,
    )
    for item in items:
        item.pedido = pedido
    ItemPedido.objects.bulk_create(items)
    return pedido


def _crear_sesion_de_stripe(request: HttpRequest, pedido: Pedido):
    stripe.api_key = settings.STRIPE_CLAVE_SECRETA
    url_de_exito = (
        request.build_absolute_uri(reverse("pagos:recibido"))
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    sesion = stripe.checkout.Session.create(
        mode="payment",
        # Managed Payments viene activo por defecto en la cuenta, pero solo
        # admite productos digitales: la documentación lista "physical goods"
        # entre las categorías no soportadas, y todos sus códigos de impuesto
        # elegibles son de software, libros, cursos o streaming. Una tienda de
        # cestería y barro no tiene forma de calificar, así que se apaga por
        # sesión. También se puede apagar por defecto en el panel de Stripe.
        managed_payments={"enabled": False},
        line_items=[
            {
                "price_data": {
                    "currency": settings.STRIPE_MONEDA,
                    "unit_amount": item.precio_unitario,
                    "product_data": {"name": item.producto.nombre},
                },
                "quantity": item.cantidad,
            }
            for item in pedido.items.select_related("producto")
        ],
        customer_email=pedido.email,
        client_reference_id=str(pedido.pk),
        # El webhook llega sin sesión ni cookies: el número de pedido tiene
        # que viajar dentro del evento.
        metadata={"pedido_id": str(pedido.pk)},
        success_url=url_de_exito,
        cancel_url=request.build_absolute_uri(reverse("pagos:cancelado")),
    )
    Pedido.objects.filter(pk=pedido.pk).update(stripe_session_id=sesion.id)
    return sesion


def iniciar_el_pago(request: HttpRequest) -> HttpResponse:
    carrito = Carrito(request)
    lineas = list(carrito)
    if not lineas:
        messages.info(request, "El carrito está vacío.")
        return redirect("pedidos:ver_carrito")

    contexto = {"lineas": lineas, "total": carrito.total}

    if request.method != "POST":
        return render(
            request,
            "pagos/checkout.html",
            {**contexto, "formulario": DatosDeEnvioForm()},
        )

    formulario = DatosDeEnvioForm(request.POST)
    if not formulario.is_valid():
        return render(
            request, "pagos/checkout.html", {**contexto, "formulario": formulario}
        )

    if not settings.STRIPE_CLAVE_SECRETA:
        messages.error(
            request,
            "El pago no está configurado: falta STRIPE_SECRET_KEY en el .env.",
        )
        return redirect("pedidos:ver_carrito")

    try:
        pedido = _crear_pedido(carrito, formulario.cleaned_data)
    except SinExistencias as error:
        messages.error(request, str(error))
        return redirect("pedidos:ver_carrito")

    try:
        sesion = _crear_sesion_de_stripe(request, pedido)
    except stripe.StripeError as error:
        # Sin sesión de pago el pedido no sirve: se descarta en vez de dejar
        # basura pendiente en el admin.
        pedido.items.all().delete()
        pedido.delete()
        messages.error(
            request, f"Stripe no aceptó la solicitud: {error.user_message or error}"
        )
        return redirect("pedidos:ver_carrito")

    # 303 para que volver atrás en el navegador no reenvíe el formulario.
    respuesta = HttpResponseRedirect(sesion.url)
    respuesta.status_code = 303
    return respuesta


def pago_recibido(request: HttpRequest) -> HttpResponse:
    """Vuelta desde Stripe. No confirma el pago: solo muestra en qué va.

    Si el webhook todavía no llegó, el pedido sigue pendiente y la página lo
    dice tal cual, en vez de dar por hecho un pago que nadie confirmó.
    """
    identificador = request.GET.get("session_id", "")
    pedido = (
        Pedido.objects.filter(stripe_session_id=identificador).first()
        if identificador
        else None
    )
    if pedido is not None:
        Carrito(request).limpiar()
    return render(request, "pagos/recibido.html", {"pedido": pedido})


def pago_cancelado(request: HttpRequest) -> HttpResponse:
    """El carrito se deja intacto a propósito: cancelar no es desistir."""
    return render(request, "pagos/cancelado.html")


def _dato(objeto, clave, por_defecto=None):
    """Lee una clave de lo que manda Stripe.

    `construct_event` devuelve un StripeObject, que acepta corchetes pero no
    `.get()`: llamarlo lanza AttributeError y tumba el webhook. Los corchetes
    con try funcionan igual sobre el StripeObject y sobre un dict común.
    """
    try:
        return objeto[clave]
    except (KeyError, TypeError):
        return por_defecto


@transaction.atomic
def _confirmar_pago(sesion) -> None:
    if _dato(sesion, "payment_status") != "paid":
        # Hay medios de pago que confirman después. Todavía no es un pago.
        return

    identificador = _dato(_dato(sesion, "metadata") or {}, "pedido_id") or _dato(
        sesion, "client_reference_id"
    )
    if not identificador:
        return

    pedido = Pedido.objects.select_for_update().filter(pk=identificador).first()
    if pedido is None or pedido.estado != Pedido.Estado.PENDIENTE:
        # Stripe reintenta los webhooks: esto tiene que poder correr dos veces
        # sin descontar el inventario dos veces.
        return

    pedido.estado = Pedido.Estado.PAGADO
    pedido.pagado_en = timezone.now()
    if not pedido.stripe_session_id:
        pedido.stripe_session_id = _dato(sesion, "id", "")
    pedido.save(update_fields=["estado", "pagado_en", "stripe_session_id"])

    # Recién acá baja el inventario. Se descuenta en la base con F() para no
    # pisar una venta simultánea, y con piso en cero por si acaso.
    for item in pedido.items.all():
        Producto.objects.filter(pk=item.producto_id).update(
            stock=Greatest(F("stock") - item.cantidad, Value(0))
        )


@csrf_exempt
@require_POST
def webhook_de_stripe(request: HttpRequest) -> HttpResponse:
    if not settings.STRIPE_SECRETO_WEBHOOK:
        return HttpResponse("Webhook sin configurar.", status=503)

    try:
        evento = stripe.Webhook.construct_event(
            request.body,
            request.META.get("HTTP_STRIPE_SIGNATURE", ""),
            settings.STRIPE_SECRETO_WEBHOOK,
        )
    except ValueError:
        return HttpResponse("Carga inválida.", status=400)
    except stripe.SignatureVerificationError:
        return HttpResponse("Firma inválida.", status=400)

    if evento["type"] == "checkout.session.completed":
        _confirmar_pago(evento["data"]["object"])

    return HttpResponse(status=200)
