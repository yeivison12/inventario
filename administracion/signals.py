from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.files.base import ContentFile
from .models import Producto, HistorialProducto

@receiver(pre_delete, sender=Producto)
def registrar_historial_producto(sender, instance, **kwargs):
    nombre_producto = instance.nombre or "Sin nombre"
    imagen_producto = None
    if instance.imagen:
        try:
            instance.imagen.open('rb')
            imagen_producto = ContentFile(instance.imagen.read(), name=instance.imagen.name)
            instance.imagen.close()
        except Exception as e:
            print(f"Error al leer la imagen: {e}")
            
    
    HistorialProducto.objects.create(
        producto=None,  
        nombre_producto=nombre_producto,
        usuario=instance.actualizado_por,  
        tipo_cambio="Eliminado",
        detalle_cambio=f"Producto <strong>'{nombre_producto}'</strong> eliminado del sistema.",
        imagen_producto=imagen_producto
    )