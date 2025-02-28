from django.contrib import admin

from administracion.models import Producto, Categoria, EmpresaNombre

# Register your models here.
admin.site.register(Producto)
admin.site.register(Categoria)
admin.site.register(EmpresaNombre)
