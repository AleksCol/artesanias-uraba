from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def ver_carrito(request: HttpRequest) -> HttpResponse:
    return render(request, "pedidos/carrito.html")
