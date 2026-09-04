from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.ver_carrito, name="ver_carrito"),
]
