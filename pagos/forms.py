from django import forms


class DatosDeEnvioForm(forms.Form):
    """Lo mínimo para despachar. Los datos de la tarjeta no pasan por acá:
    de eso se encarga Stripe Checkout en su propio dominio."""

    CLASES_DE_CAMPO = (
        "w-full border-2 border-corteza bg-hueso px-4 py-3 text-lg focus:border-selva focus:outline-none"
    )

    email = forms.EmailField(
        label="Correo electrónico",
        help_text="Ahí llega la confirmación del pedido.",
        widget=forms.EmailInput(attrs={"class": CLASES_DE_CAMPO, "autocomplete": "email"}),
    )
    direccion_de_envio = forms.CharField(
        label="Dirección de envío",
        help_text="Calle, número, barrio, municipio y un punto de referencia.",
        widget=forms.Textarea(
            attrs={"rows": 3, "class": CLASES_DE_CAMPO, "autocomplete": "street-address"}
        ),
    )
