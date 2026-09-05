from django.http import HttpRequest

from .carrito import Carrito


def resumen_del_carrito(request: HttpRequest) -> dict[str, int]:
    """Deja las unidades del carrito disponibles en todas las plantillas,
    para el contador del encabezado."""
    return {"unidades_en_el_carrito": len(Carrito(request))}
