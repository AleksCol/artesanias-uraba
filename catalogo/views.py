from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def lista_de_productos(request: HttpRequest) -> HttpResponse:
    """Portada del catálogo. Todavía sin modelos: solo confirma que el
    esqueleto responde y que las plantillas y los estilos cargan."""
    return render(request, "catalogo/lista_de_productos.html")
