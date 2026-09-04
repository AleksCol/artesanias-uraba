from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Producto


def lista_de_productos(
    request: HttpRequest, slug_de_categoria: str | None = None
) -> HttpResponse:
    """Portada del catálogo. La misma vista atiende el listado completo y el
    filtrado por categoría, que solo cambia en el queryset."""
    categoria_actual: Categoria | None = None
    productos = Producto.objects.publicados().select_related("categoria")

    if slug_de_categoria is not None:
        categoria_actual = get_object_or_404(Categoria, slug=slug_de_categoria)
        productos = productos.filter(categoria=categoria_actual)

    return render(
        request,
        "catalogo/lista_de_productos.html",
        {
            "categorias": Categoria.objects.all(),
            "categoria_actual": categoria_actual,
            "productos": productos,
        },
    )


def detalle_de_producto(request: HttpRequest, slug_del_producto: str) -> HttpResponse:
    producto = get_object_or_404(
        Producto.objects.publicados().select_related("categoria"),
        slug=slug_del_producto,
    )
    # Primero las del mismo oficio; si no hay, se completa con el resto del
    # catálogo para que la página no termine en un vacío.
    del_mismo_oficio = (
        Producto.objects.publicados()
        .filter(categoria=producto.categoria)
        .exclude(pk=producto.pk)
        .select_related("categoria")
    )
    relacionados = list(del_mismo_oficio[:3])
    if len(relacionados) < 3:
        completar = (
            Producto.objects.publicados()
            .exclude(pk=producto.pk)
            .exclude(pk__in=[otro.pk for otro in relacionados])
            .select_related("categoria")
        )
        relacionados += list(completar[: 3 - len(relacionados)])
    return render(
        request,
        "catalogo/detalle_de_producto.html",
        {"producto": producto, "relacionados": relacionados},
    )
