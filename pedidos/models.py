from django.db import models

from catalogo.models import Producto


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de pago"
        PAGADO = "pagado", "Pagado"
        ENVIADO = "enviado", "Enviado"

    email = models.EmailField("correo del comprador")
    direccion_de_envio = models.TextField("dirección de envío")
    # En centavos. Grande a propósito: un pedido de varias hamacas se pasa
    # del tope de un entero normal medido en centavos de peso.
    total = models.PositiveBigIntegerField(
        help_text="En centavos, congelado al crear el pedido."
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE, db_index=True
    )
    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    creado = models.DateTimeField(auto_now_add=True)
    # Lo escribe el webhook, no la vuelta del navegador.
    pagado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creado", "-id"]

    def __str__(self) -> str:
        return f"Pedido {self.pk} · {self.email}"

    @property
    def esta_pagado(self) -> bool:
        return self.estado in {self.Estado.PAGADO, self.Estado.ENVIADO}


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="items", on_delete=models.CASCADE)
    # PROTECT: no se puede borrar un producto que ya alguien compró, o el
    # pedido quedaría sin poder decir qué se vendió.
    producto = models.ForeignKey(
        Producto, related_name="items_de_pedido", on_delete=models.PROTECT
    )
    cantidad = models.PositiveIntegerField()
    # Copia del precio al momento de la compra: si mañana sube, este pedido
    # tiene que seguir diciendo lo que se cobró.
    precio_unitario = models.PositiveIntegerField(
        help_text="En centavos, al momento de la compra."
    )

    class Meta:
        verbose_name = "ítem del pedido"
        verbose_name_plural = "ítems del pedido"

    def __str__(self) -> str:
        return f"{self.cantidad} × {self.producto.nombre}"

    @property
    def subtotal(self) -> int:
        """En centavos."""
        return self.cantidad * self.precio_unitario
