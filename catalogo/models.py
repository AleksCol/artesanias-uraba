from django.db import models
from django.urls import reverse


class Categoria(models.Model):
    """Agrupación por oficio o material: cestería, talla en madera, barro..."""

    nombre = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Se usa en la dirección web de la categoría.",
    )

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre

    def get_absolute_url(self) -> str:
        return reverse("catalogo:productos_por_categoria", args=[self.slug])


class ProductoQuerySet(models.QuerySet):
    def publicados(self) -> "ProductoQuerySet":
        """Los que el dueño marcó como visibles en la tienda."""
        return self.filter(activo=True)

    def con_existencias(self) -> "ProductoQuerySet":
        return self.filter(stock__gt=0)


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text="Se usa en la dirección web del producto.",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="categoría",
    )
    descripcion = models.TextField("descripción", blank=True)
    # El precio se guarda en centavos porque es la unidad que espera Stripe.
    # Evita además los errores de redondeo de los flotantes.
    precio = models.PositiveIntegerField(
        help_text="En centavos de peso. Un producto de $80.000 se guarda como 8000000.",
    )
    stock = models.PositiveIntegerField("existencias", default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True)
    activo = models.BooleanField(
        default=True,
        help_text="Desmárcalo para ocultar el producto de la tienda sin borrarlo.",
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = ProductoQuerySet.as_manager()

    class Meta:
        ordering = ["-creado", "-id"]
        indexes = [
            models.Index(fields=["activo", "categoria"]),
        ]

    def __str__(self) -> str:
        return self.nombre

    def get_absolute_url(self) -> str:
        return reverse("catalogo:detalle_de_producto", args=[self.slug])

    @property
    def precio_en_pesos(self) -> int:
        """El precio en pesos enteros, para mostrarlo. En Colombia no se
        manejan centavos en la práctica."""
        return self.precio // 100

    @property
    def hay_existencias(self) -> bool:
        return self.stock > 0
