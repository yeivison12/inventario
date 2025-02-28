from django.db import models
from django.contrib.auth.models import User
from administracion.models import Producto

class Venta(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    cliente = models.CharField(max_length=100)
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE)
    productos = models.ManyToManyField(Producto, through='VentaProducto')
    metodo_pago = models.CharField(
        max_length=20, 
        choices=METODO_PAGO_CHOICES, 
        default='efectivo'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas_creadas'
    )
    actualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas_actualizadas'
    )

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente}"

    def actualizar_total(self):
        self.total = sum(item.subtotal for item in self.ventaproducto_set.all())
        self.save(update_fields=['total'])

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.pk and user:
            self.creado_por = user
        if user:
            self.actualizado_por = user
        super().save(*args, **kwargs)


class VentaProducto(models.Model):
    venta = models.ForeignKey(
        Venta, 
        on_delete=models.CASCADE, 
        related_name='ventaproducto_set'
    )
    # Se usa SET_NULL para que, si se elimina el producto, no se borre este registro.
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    # Campo desnormalizado para guardar el nombre del producto al momento de la venta.
    nombre_producto = models.CharField(
        max_length=100, 
        editable=False, 
        default='Producto eliminado'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Si existe un producto y no se ha asignado el nombre, lo copiamos.
        if self.producto:
            self.nombre_producto = self.producto.nombre
            
            # Si el precio no está asignado o es 0, se toma del producto.
            if not self.precio or self.precio == 0:
                self.precio = self.producto.precio

        # Calculamos el subtotal
        self.subtotal = self.cantidad * self.precio

        # Si es un registro nuevo (no existe self.pk) y el producto no es None,
        # descontamos el stock del producto.
        if not self.pk and self.producto:
            self.producto.cantidad -= self.cantidad
            self.producto.save()

        super().save(*args, **kwargs)
        self.venta.actualizar_total()

    def __str__(self):
        # Se muestra el nombre desnormalizado o el texto por defecto si está vacío
        return f"{self.cantidad}x {self.nombre_producto}"
