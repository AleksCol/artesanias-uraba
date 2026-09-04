"""Carga un catálogo de muestra para poder ver la tienda con contenido.

Las fotografías se bajan de Pexels, cuya licencia permite uso comercial sin
atribución. Son fotos de referencia, no de las piezas reales: cuando haya
producto de verdad, se reemplazan desde el admin.
"""

import urllib.request
from typing import Any

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalogo.models import Categoria, Producto

PLANTILLA_DE_FOTO = (
    "https://images.pexels.com/photos/{id}/pexels-photo-{id}.jpeg"
    "?auto=compress&cs=tinysrgb&w=1600"
)

CATEGORIAS = {
    "ceramica": "Cerámica y barro",
    "cesteria": "Cestería en fibra",
    "madera": "Talla en madera",
    "tejido": "Tejido y hamacas",
}

# (clave de categoría, nombre, precio en centavos, stock, id de la foto, descripción)
#
# El orden importa: el listado va de más nuevo a más viejo, así que esta lista
# se ve al revés en la tienda. Está armada para que las dos fotos apaisadas
# —la talla y la hamaca— caigan en las franjas anchas de la grilla.
PRODUCTOS = [
    (
        "cesteria", "Sombrero trenzado en caña flecha", 21000000, 0, 6843270,
        "Trenza de quince pares, la más cerrada que se teje por acá.\n"
        "Se enrolla sin perder la forma.",
    ),
    (
        "ceramica", "Múcuras pintadas a mano", 18500000, 6, 33926932,
        "Juego de tres múcuras de barro rojo, torneadas y pintadas con "
        "engobes minerales.\nCada franja se traza a pulso, así que no hay dos "
        "iguales.",
    ),
    (
        "tejido", "Hamaca de hilo de Necoclí", 42000000, 2, 3255245,
        "Tejida en telar de horqueta con hilo de algodón mercerizado.\n"
        "Dos metros y medio de largo, con brazos de macramé anudados a mano.\n"
        "Soporta hasta 150 kilos.",
    ),
    (
        "cesteria", "Canasto tejido en iraca", 13000000, 4, 33476890,
        "Fibra de iraca cosechada y secada al sol antes de tejerla.\n"
        "Ocho días de trabajo por pieza.",
    ),
    (
        "ceramica", "Par de vasijas de barro negro", 24000000, 3, 5377308,
        "Quemadas por reducción, que es lo que les da el negro: se tapa el "
        "horno y el humo entra en la arcilla.\nQuedan impermeables sin esmalte.",
    ),
    (
        "madera", "Tabla tallada en relieve", 32000000, 1, 4611339,
        "Tallada en una sola pieza de madera de la región y terminada con "
        "aceite de linaza.\nEl relieve se trabaja a gubia, sin plantilla.",
    ),
    (
        "madera", "Juego de cucharas en teca", 7200000, 9, 350417,
        "Seis piezas talladas en teca de plantaciones de la zona.\n"
        "Sin barniz: se curan con aceite de cocina y duran años.",
    ),
    (
        "ceramica", "Cántaro de barro crudo", 9500000, 5, 11975310,
        "Levantado a rollo y bruñido con piedra de río antes de la quema.\n"
        "Mantiene el agua fresca por evaporación.",
    ),
]


class Command(BaseCommand):
    help = "Crea categorías y productos de muestra, con fotos de Pexels."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--borrar-todo",
            action="store_true",
            help="Borra todos los productos y categorías antes de cargar.",
        )
        parser.add_argument(
            "--sin-fotos",
            action="store_true",
            help="No descarga imágenes (útil sin conexión).",
        )

    def handle(self, *args: Any, **opciones: Any) -> None:
        if opciones["borrar_todo"]:
            productos_borrados = Producto.objects.all().delete()[0]
            categorias_borradas = Categoria.objects.all().delete()[0]
            self.stdout.write(
                f"Borrados {productos_borrados} productos y "
                f"{categorias_borradas} categorías."
            )

        categorias: dict[str, Categoria] = {}
        for clave, nombre in CATEGORIAS.items():
            categoria, creada = Categoria.objects.get_or_create(
                slug=slugify(nombre), defaults={"nombre": nombre}
            )
            categorias[clave] = categoria
            self.stdout.write(f"{'+' if creada else '='} categoría {nombre}")

        for clave, nombre, precio, stock, id_foto, descripcion in PRODUCTOS:
            producto, creado = Producto.objects.update_or_create(
                slug=slugify(nombre),
                defaults={
                    "nombre": nombre,
                    "categoria": categorias[clave],
                    "descripcion": descripcion,
                    "precio": precio,
                    "stock": stock,
                    "activo": True,
                },
            )
            self.stdout.write(f"{'+' if creado else '='} {nombre}")

            if opciones["sin_fotos"] or producto.imagen:
                continue
            try:
                peticion = urllib.request.Request(
                    PLANTILLA_DE_FOTO.format(id=id_foto),
                    headers={"User-Agent": "artesanias-uraba/1.0"},
                )
                with urllib.request.urlopen(peticion, timeout=60) as respuesta:
                    contenido = respuesta.read()
            except Exception as error:  # noqa: BLE001 - una foto no debe tumbar la carga
                self.stderr.write(f"  no se pudo bajar la foto de {nombre}: {error}")
                continue
            producto.imagen.save(
                f"{producto.slug}.jpg", ContentFile(contenido), save=True
            )
            self.stdout.write(f"  foto guardada ({len(contenido) // 1024} KB)")

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo: {Categoria.objects.count()} categorías, "
                f"{Producto.objects.count()} productos."
            )
        )
