from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from catalogo.formato import formato_de_pesos

from .models import ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ["producto", "cantidad", "precio_mostrado", "subtotal_mostrado"]
    readonly_fields = ["producto", "cantidad", "precio_mostrado", "subtotal_mostrado"]
    can_delete = False

    @admin.display(description="precio unitario")
    def precio_mostrado(self, item: ItemPedido) -> str:
        return formato_de_pesos(item.precio_unitario)

    @admin.display(description="subtotal")
    def subtotal_mostrado(self, item: ItemPedido) -> str:
        return formato_de_pesos(item.subtotal)

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        # Las líneas se crean en el checkout, no a mano: cambiarlas acá
        # dejaría el total del pedido mintiendo.
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "total_mostrado",
        "estado",
        "creado",
        "pagado_en",
    ]
    list_display_links = ["id", "email"]
    list_filter = ["estado", "creado"]
    search_fields = ["id", "email", "stripe_session_id"]
    date_hierarchy = "creado"
    inlines = [ItemPedidoInline]
    readonly_fields = [
        "total_mostrado",
        "stripe_session_id",
        "creado",
        "pagado_en",
        "enlace_a_stripe",
    ]
    fieldsets = [
        ("Comprador", {"fields": ["email", "direccion_de_envio"]}),
        ("Estado", {"fields": ["estado", "total_mostrado", "creado", "pagado_en"]}),
        ("Stripe", {"fields": ["stripe_session_id", "enlace_a_stripe"]}),
    ]

    @admin.display(description="total", ordering="total")
    def total_mostrado(self, pedido: Pedido) -> str:
        return formato_de_pesos(pedido.total)

    @admin.display(description="ver en Stripe")
    def enlace_a_stripe(self, pedido: Pedido) -> str:
        if not pedido.stripe_session_id:
            return "Todavía sin sesión de pago."
        return format_html(
            '<a href="https://dashboard.stripe.com/test/payments" target="_blank" '
            'rel="noopener">Panel de pruebas de Stripe</a> · sesión '
            "<code>{}</code>",
            pedido.stripe_session_id,
        )

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Un pedido nace del checkout. Crearlo a mano no tendría pago detrás.
        return False
