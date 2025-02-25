from django import forms
from .models import Venta, VentaProducto

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente']
        widgets = {
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
        }
class VentaProductoForm(forms.ModelForm):
    class Meta:
        model = VentaProducto
        fields = ['producto', 'cantidad']

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')

        if cantidad is None:
            raise forms.ValidationError("Debe ingresar una cantidad para cada producto.")

        if cantidad <= 0:
            raise forms.ValidationError("La cantidad debe ser mayor a 0.")

        if producto and cantidad:
            if cantidad > producto.cantidad:
                raise forms.ValidationError(
                    f"No hay suficiente stock para {producto.nombre}. Stock disponible: {producto.cantidad}."
                )

        return cleaned_data
