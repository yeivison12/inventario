#!/usr/bin/env python
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime

# Función auxiliar para simular django.utils.timezone.localtime
def localtime(dt):
    return dt

# Creamos una clase dummy para simular HttpResponse
class DummyHttpResponse(BytesIO):
    def __init__(self, content_type='application/pdf'):
        super().__init__()
        self.headers = {}
        self.content_type = content_type

    def __setitem__(self, key, value):
        self.headers[key] = value

# Clases dummy para simular modelos y relaciones
class User:
    def __init__(self, username):
        self.username = username

class DummyRelatedManager:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items

    def count(self):
        return len(self.items)

class VentaProducto:
    def __init__(self, nombre_producto, cantidad, subtotal):
        self.nombre_producto = nombre_producto
        self.cantidad = cantidad
        self.subtotal = subtotal

class Venta:
    def __init__(self, id, cliente, vendedor, fecha_creacion, productos):
        self.id = id
        self.cliente = cliente
        self.vendedor = vendedor
        self.fecha_creacion = fecha_creacion
        self.ventaproducto_set = DummyRelatedManager(productos)

class EmpresaNombre:
    def __init__(self, nombre, nit=None):
        self.nombre = nombre
        self.nit = nit

# Simulamos un "manager" al estilo Django para poder usar .get() y .first()
class DummyQuerySet:
    def __init__(self, items):
        self.items = items

    def get(self, pk):
        for item in self.items:
            if item.id == pk:
                return item
        raise ValueError("Objeto no encontrado")

    def first(self):
        return self.items[0] if self.items else None

# La función original, adaptada para usar los objetos dummy
def generar_ticket_venta(request, pk):
    # Recupera la venta y la empresa desde nuestros "managers" dummy
    venta = Venta.objects.get(pk)
    empresa = EmpresaNombre.objects.first()
    num_products = venta.ventaproducto_set.count()

    def format_price(price):
        price = float(price)
        if price % 1 == 0:
            return f"${int(price):,}"
        else:
            return f"${price:,.2f}"

    # Cálculo dinámico de la altura del ticket
    altura_fija = 85      # Altura base en mm (elementos fijos)
    altura_por_producto = 5   # Altura por producto en mm
    sum_deltas = (altura_fija + altura_por_producto * num_products) * mm
    ticket_height = sum_deltas + 10 * mm  # Margen superior adicional
    ticket_width = 80 * mm

    response = DummyHttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_venta_{venta.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=(ticket_width, ticket_height))
    y = ticket_height - 10 * mm  # Margen superior inicial

    # Encabezado
    pdf.setFont("Courier-Bold", 10)
    pdf.drawCentredString(ticket_width / 2, y, f"{empresa.nombre}")
    y -= 5 * mm
    if empresa.nit:
        pdf.drawCentredString(ticket_width / 2, y, f"NIT:{empresa.nit}")
    else:
        pdf.drawCentredString(ticket_width / 2, y, "NIT: N/A")
    y -= 5 * mm
    pdf.drawCentredString(ticket_width / 2, y, localtime(venta.fecha_creacion).strftime('%Y-%m-%d %H:%M'))

    y -= 10 * mm

    # Datos cliente/vendedor
    pdf.setFont("Courier", 9)
    pdf.drawString(5 * mm, y, f"Cliente: {venta.cliente}")
    y -= 5 * mm
    pdf.drawString(5 * mm, y, f"Vendedor: {venta.vendedor.username}")
    y -= 10 * mm

    # Separador
    pdf.drawString(5 * mm, y, "-" * 32)
    y -= 5 * mm

    # Encabezado productos
    pdf.setFont("Courier-Bold", 9)
    pdf.drawString(5 * mm, y, "Cant   Producto       Subtotal")
    y -= 5 * mm
    pdf.drawString(5 * mm, y, "-" * 32)
    y -= 5 * mm

    # Listado de productos
    pdf.setFont("Courier", 9)
    for item in venta.ventaproducto_set.all():
        producto = (item.nombre_producto[:12] if item.nombre_producto else "Producto eliminado").ljust(15)
        cantidad = str(item.cantidad).rjust(2)
        subtotal = format_price(item.subtotal).rjust(8)
        pdf.drawString(5 * mm, y, f"{cantidad}     {producto}{subtotal}")
        y -= 5 * mm

    # Total
    total_venta = sum(i.subtotal for i in venta.ventaproducto_set.all())
    pdf.drawString(5 * mm, y, "-" * 32)
    y -= 5 * mm
    pdf.setFont("Courier-Bold", 10)
    pdf.drawString(5 * mm, y, f"TOTAL:".ljust(20) + format_price(total_venta).rjust(8))
    y -= 10 * mm
    # Mensaje final
    pdf.setFont("Courier", 9)
    pdf.drawCentredString(ticket_width / 2, y, f"Gracias por su compra {venta.cliente}!")
    y -= 5 * mm
    pdf.setFont("Courier-Bold", 10)
    pdf.drawCentredString(ticket_width / 2, y, f"{empresa.nombre}")

    pdf.save()
    return response

# Función principal que configura los datos dummy y ejecuta la generación del ticket
def run_ticket_test():
    # Crear un usuario dummy para el vendedor
    vendedor = User("vendedor")
    
    # Crear la empresa dummy
    empresa = EmpresaNombre("Mi Empresa", nit="123456789")
    
    # Crear 900 productos dummy
    productos = [VentaProducto(f"Producto {i+1}", 1, 100.00) for i in range(900)]
    
    # Crear una venta dummy (con id=1) que incluye los 900 productos
    venta = Venta(1, "Cliente Test", vendedor, datetime.now(), productos)
    
    # Asignar los "managers" dummy a las clases para simular el ORM de Django
    Venta.objects = DummyQuerySet([venta])
    EmpresaNombre.objects = DummyQuerySet([empresa])
    
    # "Request" dummy (no se utiliza en la función)
    request = object()
    
    # Generar el ticket en PDF
    response = generar_ticket_venta(request, 1)
    
    # Guardar el PDF en disco
    filename = f"ticket_venta_{venta.id}.pdf"
    with open(filename, "wb") as f:
        f.write(response.getvalue())
    
    print(f"PDF generado y guardado como: {filename}")

if __name__ == "__main__":
    run_ticket_test()
