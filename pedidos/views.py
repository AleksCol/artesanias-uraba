from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogo.formato import formato_de_pesos
from catalogo.models import Producto

from .carrito import Carrito
from .forms import AgregarAlCarritoForm


def _es_peticion_asincrona(request: HttpRequest) -> bool:
    """El JS del botón manda esta cabecera. Sin JS, el formulario se envía
    normal y la vista responde con una redirección de toda la vida."""
    return request.headers.get("X-Peticion-Asincrona") == "1"


def _respuesta_del_carrito(carrito: Carrito, aviso: str) -> JsonResponse:
    return JsonResponse(
        {
            "unidades": len(carrito),
            "total": formato_de_pesos(carrito.total),
            "aviso": aviso,
        }
    )


def ver_carrito(request: HttpRequest) -> HttpResponse:
    carrito = Carrito(request)
    lineas = list(carrito)
    return render(
        request,
        "pedidos/carrito.html",
        {
            "lineas": lineas,
            "total": carrito.total,
            "unidades": len(carrito),
        },
    )


@require_POST
def agregar_al_carrito(request: HttpRequest, producto_id: int) -> HttpResponse:
    carrito = Carrito(request)
    producto = get_object_or_404(Producto.objects.publicados(), pk=producto_id)
    formulario = AgregarAlCarritoForm(request.POST)

    if not formulario.is_valid():
        aviso = "No se pudo agregar: la cantidad no es válida."
        if _es_peticion_asincrona(request):
            return _respuesta_del_carrito(carrito, aviso)
        messages.error(request, aviso)
        return redirect(producto.get_absolute_url())

    resultado = carrito.agregar(
        producto,
        formulario.cleaned_data["cantidad"],
        sobrescribir=formulario.cleaned_data["sobrescribir"],
    )

    if producto.stock == 0:
        aviso, nivel = f"{producto.nombre} está agotado.", messages.error
    elif resultado.se_recorto:
        aviso, nivel = (
            f"Solo quedaban {producto.stock} de {producto.nombre}.",
            messages.warning,
        )
    else:
        aviso, nivel = f"{producto.nombre} está en el carrito.", messages.success

    if _es_peticion_asincrona(request):
        return _respuesta_del_carrito(carrito, aviso)

    nivel(request, aviso)
    return redirect("pedidos:ver_carrito")


@require_POST
def actualizar_cantidad(request: HttpRequest, producto_id: int) -> HttpResponse:
    carrito = Carrito(request)
    producto = get_object_or_404(Producto.objects.publicados(), pk=producto_id)
    formulario = AgregarAlCarritoForm(request.POST)

    if formulario.is_valid():
        resultado = carrito.agregar(
            producto, formulario.cleaned_data["cantidad"], sobrescribir=True
        )
        if resultado.se_recorto:
            messages.warning(
                request, f"Solo quedan {producto.stock} de {producto.nombre}."
            )
    else:
        messages.error(request, "La cantidad no es válida.")
    return redirect("pedidos:ver_carrito")


@require_POST
def quitar_del_carrito(request: HttpRequest, producto_id: int) -> HttpResponse:
    carrito = Carrito(request)
    producto = get_object_or_404(Producto, pk=producto_id)
    carrito.quitar(producto)
    messages.success(request, f"Se quitó {producto.nombre} del carrito.")
    return redirect("pedidos:ver_carrito")
