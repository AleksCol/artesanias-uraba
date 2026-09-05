"""El carrito vive en la sesión, no en la base de datos.

No se pide cuenta para comprar, así que no hay a quién colgarle un carrito
persistente. En la sesión se guarda solo la cantidad por producto; el precio
se lee siempre de la base, para que un carrito viejo no muestre un precio que
ya cambió. El precio se congela al crear el pedido, no antes.
"""

from dataclasses import dataclass
from typing import Iterator

from django.conf import settings
from django.http import HttpRequest

from catalogo.models import Producto


@dataclass
class ResultadoDeAgregar:
    """Lo que quedó en el carrito y si hubo que recortar por existencias."""

    cantidad_final: int
    se_recorto: bool


@dataclass
class LineaDelCarrito:
    producto: Producto
    cantidad: int

    @property
    def subtotal(self) -> int:
        """En centavos."""
        return self.producto.precio * self.cantidad


class Carrito:
    def __init__(self, request: HttpRequest) -> None:
        self.sesion = request.session
        # Ojo: leer el carrito no debe escribir en la sesión. Si se escribiera
        # acá, cada visita anónima crearía una fila de sesión en la base solo
        # por pintar el contador del encabezado.
        self.contenido: dict[str, dict[str, int]] = (
            self.sesion.get(settings.CARRITO_SESSION_ID) or {}
        )

    def agregar(
        self, producto: Producto, cantidad: int = 1, sobrescribir: bool = False
    ) -> ResultadoDeAgregar:
        """Agrega o fija la cantidad, sin pasarse de las existencias.

        El recorte se calcula acá, que es donde se conocen a la vez la cantidad
        que ya había y la que se pidió. Calcularlo afuera fue un error: con el
        carrito ya en el tope, sumar más daba "todo bien" en vez de avisar.
        """
        clave = str(producto.pk)
        actual = self.contenido.get(clave, {}).get("cantidad", 0)
        pedida = cantidad if sobrescribir else actual + cantidad
        final = max(0, min(pedida, producto.stock))

        if final == 0:
            self.contenido.pop(clave, None)
        else:
            self.contenido[clave] = {"cantidad": final}
        self.guardar()
        return ResultadoDeAgregar(cantidad_final=final, se_recorto=final < pedida)

    def quitar(self, producto: Producto) -> None:
        if self.contenido.pop(str(producto.pk), None) is not None:
            self.guardar()

    def limpiar(self) -> None:
        self.contenido = {}
        self.guardar()

    def guardar(self) -> None:
        self.sesion[settings.CARRITO_SESSION_ID] = self.contenido
        self.sesion.modified = True

    def __iter__(self) -> Iterator[LineaDelCarrito]:
        productos = {
            str(producto.pk): producto
            for producto in Producto.objects.publicados()
            .filter(pk__in=self.contenido.keys())
            .select_related("categoria")
        }

        # Un producto despublicado o borrado no puede quedar en el carrito.
        desaparecidos = set(self.contenido) - set(productos)
        if desaparecidos:
            for clave in desaparecidos:
                del self.contenido[clave]
            self.guardar()

        for clave, producto in productos.items():
            cantidad = min(self.contenido[clave]["cantidad"], producto.stock)
            if cantidad != self.contenido[clave]["cantidad"]:
                # Se vendió inventario desde que se agregó: se ajusta.
                self.contenido[clave]["cantidad"] = cantidad
                self.guardar()
            if cantidad > 0:
                yield LineaDelCarrito(producto=producto, cantidad=cantidad)

    def __len__(self) -> int:
        """Unidades totales, no líneas distintas."""
        return sum(linea["cantidad"] for linea in self.contenido.values())

    @property
    def total(self) -> int:
        """En centavos."""
        return sum(linea.subtotal for linea in self)

    @property
    def esta_vacio(self) -> bool:
        return len(self) == 0
