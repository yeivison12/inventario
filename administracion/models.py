from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marcas_creadas')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marcas_actualizadas')

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and user:
            self.creado_por = user
        if user:
            self.actualizado_por = user
        super().save(*args, **kwargs)
    def __str__(self):
            return self.nombre
    
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='categoria')  
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_creados')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_actualizados')

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and user:
            self.creado_por = user
        if user:
            self.actualizado_por = user

        # Si hay una imagen, la procesamos para reducir su tamaño
        if self.imagen:
            try:
                img = Image.open(self.imagen)
                # Definimos el tamaño máximo (en píxeles)
                max_size = (800, 800)
                if img.height > max_size[1] or img.width > max_size[0]:
                    img.thumbnail(max_size, Image.ANTIALIAS)
                    # Guardamos la imagen en un buffer en memoria
                    buffer = BytesIO()
                    # Determinar el formato: JPEG o PNG
                    img_format = 'JPEG' if img.format and img.format.upper() == 'JPEG' else 'PNG'
                    img.save(buffer, format=img_format, quality=85)
                    buffer.seek(0)
                    # Reemplazamos el archivo original por la imagen procesada
                    self.imagen = ContentFile(buffer.read(), name=self.imagen.name)
            except Exception as e:
                print(f"Error al procesar la imagen: {e}")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
class EmpresaNombre(models.Model):
    nombre = models.CharField(max_length=25,blank=True, null=True, default="Tu empresa")
    nit = models.IntegerField( null=True,blank=True,default='123456789')
    correo = models.EmailField(max_length=50,blank=True, null=True)
    logo = models.ImageField(upload_to='empresa/', blank=True, null=True)
    
class HistorialProducto(models.Model):
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL,
        null=True,  
        blank=True
    )
    nombre_producto = models.CharField(max_length=255)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_cambio = models.CharField(max_length=50)
    detalle_cambio = models.TextField()
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    imagen_producto = models.ImageField(upload_to='historial/', null=True, blank=True)