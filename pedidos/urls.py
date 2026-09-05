from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.ver_carrito, name="ver_carrito"),
    path("agregar/<int:producto_id>/", views.agregar_al_carrito, name="agregar"),
    path("actualizar/<int:producto_id>/", views.actualizar_cantidad, name="actualizar"),
    path("quitar/<int:producto_id>/", views.quitar_del_carrito, name="quitar"),
]
