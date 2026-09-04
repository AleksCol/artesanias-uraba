from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.lista_de_productos, name="lista_de_productos"),
]
