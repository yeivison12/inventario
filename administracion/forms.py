from django import forms
from .models import Producto, Categoria, EmpresaNombre

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'precio', 'cantidad', 'descripcion', 'categoria', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Precio'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cantidad disponible'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del producto'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={
            'class': 'form-select mb-3',
            'id': 'horario',
            'required': True
        }),

        }
        labels = {
            'nombre': 'Nombre',
            'precio': 'Precio ($)',
            'cantidad': 'Cantidad',
            'descripcion': 'Descripción',
            'imagen': 'Imagen',
            'categoria': 'Categoría',
        }

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la marca'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre': 'Nombre',
            'imagen': 'Imagen',
        }
class NombreEmpresaForm(forms.ModelForm):
    class Meta:
        model = EmpresaNombre
        fields = ['nombre','correo', 'logo','nit']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de tu empresa'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo(opcional)'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'nit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder':'Nit'})
        }
        labels = {
            'nombre': 'Nombre',
            'logo': 'Imagen',
            'correo':'Correo Electronico',
            'nit': 'NIT',
        }        