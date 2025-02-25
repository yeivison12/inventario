from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import VentaProducto

@receiver(post_delete, sender=VentaProducto)
def devolver_stock(sender, instance, **kwargs):
    """
    Al eliminar un detalle de venta, se suma la cantidad vendida al stock del producto
    y se actualiza el total de la venta.
    """
    instance.producto.cantidad += instance.cantidad
    instance.producto.save()
    instance.venta.actualizar_total()