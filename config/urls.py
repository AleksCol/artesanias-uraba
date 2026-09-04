from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# El panel de administración es el admin de Django, no un panel aparte.
admin.site.site_header = "Artesanías de Urabá"
admin.site.site_title = "Artesanías de Urabá"
admin.site.index_title = "Gestión de productos y pedidos"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("django.contrib.auth.urls")),
    path("carrito/", include("pedidos.urls")),
    path("pagos/", include("pagos.urls")),
    path("", include("catalogo.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
