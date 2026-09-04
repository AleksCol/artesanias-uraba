from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from .formato import formato_de_pesos
from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "cantidad_de_productos"]
    search_fields = ["nombre"]
    prepopulated_fields = {"slug": ["nombre"]}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Categoria]:
        return super().get_queryset(request).annotate(total=Count("productos"))

    @admin.display(description="productos", ordering="total")
    def cantidad_de_productos(self, categoria: Categoria) -> int:
        return categoria.total


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        "nombre",
        "categoria",
        "precio_mostrado",
        "stock",
        "activo",
        "creado",
    ]
    list_display_links = ["nombre"]
    list_editable = ["stock", "activo"]
    list_filter = ["activo", "categoria"]
    list_select_related = ["categoria"]
    search_fields = ["nombre", "descripcion"]
    prepopulated_fields = {"slug": ["nombre"]}
    readonly_fields = ["vista_previa", "creado", "actualizado"]
    fieldsets = [
        (None, {"fields": ["nombre", "slug", "categoria", "descripcion"]}),
        ("Venta", {"fields": ["precio", "stock", "activo"]}),
        ("Imagen", {"fields": ["imagen", "vista_previa"]}),
        ("Fechas", {"fields": ["creado", "actualizado"], "classes": ["collapse"]}),
    ]

    @admin.display(description="precio", ordering="precio")
    def precio_mostrado(self, producto: Producto) -> str:
        return formato_de_pesos(producto.precio)

    @admin.display(description="vista previa")
    def vista_previa(self, producto: Producto) -> str:
        if not producto.imagen:
            return "Sin imagen todavía."
        return format_html(
            '<img src="{}" style="max-height:220px;border-radius:2px">',
            producto.imagen.url,
        )
