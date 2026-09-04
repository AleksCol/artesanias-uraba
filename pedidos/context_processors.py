from django.conf import settings
from django.http import HttpRequest


def resumen_del_carrito(request: HttpRequest) -> dict[str, int]:
    """Deja disponible en todas las plantillas cuántas unidades hay en el
    carrito, para el contador del encabezado."""
    carrito = request.session.get(settings.CARRITO_SESSION_ID, {})
    unidades = sum(linea.get("cantidad", 0) for linea in carrito.values())
    return {"unidades_en_el_carrito": unidades}
