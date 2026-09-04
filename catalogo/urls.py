from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.lista_de_productos, name="lista_de_productos"),
    path(
        "categoria/<slug:slug_de_categoria>/",
        views.lista_de_productos,
        name="productos_por_categoria",
    ),
    path(
        "producto/<slug:slug_del_producto>/",
        views.detalle_de_producto,
        name="detalle_de_producto",
    ),
]
