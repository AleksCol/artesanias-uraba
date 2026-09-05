from django import forms


class AgregarAlCarritoForm(forms.Form):
    # Sin tope propio: el único límite real son las existencias, y de eso
    # se encarga el carrito. Dos topes distintos se contradicen.
    cantidad = forms.IntegerField(min_value=1, initial=1)
    # Al agregar desde el detalle se suma; al editar desde el carrito se fija.
    sobrescribir = forms.BooleanField(
        required=False, initial=False, widget=forms.HiddenInput
    )
