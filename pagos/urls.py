from django.urls import path

from . import views

app_name = "pagos"

urlpatterns = [
    path("checkout/", views.iniciar_el_pago, name="iniciar"),
    path("listo/", views.pago_recibido, name="recibido"),
    path("cancelado/", views.pago_cancelado, name="cancelado"),
    path("webhook/", views.webhook_de_stripe, name="webhook"),
]
