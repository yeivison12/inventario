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
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='ventaproducto_set')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Si no se asigna un precio, se toma el precio del producto
        if not self.precio or self.precio == 0:
            self.precio = self.producto.precio

        # Calcular el subtotal
        self.subtotal = self.cantidad * self.precio

        # Si es un nuevo registro, descontar el stock del producto
        if not self.pk:
            self.producto.cantidad -= self.cantidad
            self.producto.save()

        super().save(*args, **kwargs)
        self.venta.actualizar_total()

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
