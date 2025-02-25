# test.py

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
from collections import namedtuple
import random

def generate_pdf(queryset):
    """Genera el PDF a partir del queryset con un diseño de tabla mejorado."""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="ventas.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    page_number = 1

    # Ajustamos el alto de cada fila para dar más espacio al texto
    row_height = 25
    margin_bottom = 80  # Espacio reservado para el footer

    # Definimos estilos
    styles = {
        'title': {'font': 'Helvetica-Bold', 'size': 18, 'color': (0.2, 0.4, 0.6)},
        'header': {'font': 'Helvetica-Bold', 'size': 12, 'color': (1, 1, 1)},  # Texto blanco para el header
        'body': {'font': 'Helvetica', 'size': 10, 'color': (0.2, 0.2, 0.2)},
        'accent': {'color': (0.2, 0.4, 0.6)},  # Color principal
        'row_color': (0.95, 0.95, 0.95)       # Color de fondo para todas las filas
    }

    def draw_header():
        """Dibuja el título y la línea superior."""
        pdf.setFont(styles['title']['font'], styles['title']['size'])
        pdf.setFillColorRGB(*styles['title']['color'])
        pdf.drawString(40, height - 50, "Reporte de Ventas Detallado")
        pdf.setFont(styles['body']['font'], styles['body']['size'])
        pdf.setFillColorRGB(*styles['body']['color'])
        pdf.drawString(40, height - 70, f"Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        pdf.line(40, height - 75, width - 40, height - 75)

    def draw_footer():
        """Dibuja el número de página y la línea inferior."""
        pdf.setFont(styles['body']['font'], 8)
        pdf.setFillColorRGB(0.4, 0.4, 0.4)
        pdf.drawCentredString(width / 2, 30, f"Página {page_number} | Generado por Sistema de Inventario Dassy Yurany")
        pdf.line(40, 40, width - 40, 40)

    def draw_table_header(y):
        """Dibuja la cabecera de la tabla con un rectángulo de fondo."""
        # Fondo del encabezado
        pdf.setFillColorRGB(*styles['accent']['color'])
        pdf.rect(40, y - row_height, width - 80, row_height, fill=1)

        # Texto de cabecera
        pdf.setFont(styles['header']['font'], styles['header']['size'])
        pdf.setFillColorRGB(*styles['header']['color'])

        headers = ["ID", "Cliente", "Vendedor", "Total", "Fecha"]
        # Posiciones aproximadas (ajusta si deseas columnas más anchas)
        x_positions = [50, 100, 250, 355, 468]

        # Dibuja cada texto un poco más abajo para centrar verticalmente
        for i, header in enumerate(headers):
            pdf.drawString(x_positions[i], y - (row_height / 1.5), header)

        return y - row_height  # Ajustamos el y para la siguiente fila

    # Dibujamos el header inicial de la página
    draw_header()
    y_position = draw_table_header(height - 100)

    total_ventas = 0
    row_counter = 0  # Contador de filas por página

    for venta in queryset:
        # Verificar si hay espacio suficiente para la siguiente fila + footer
        if y_position < margin_bottom + row_height:
            # Dibujar footer y pasar a la siguiente página
            draw_footer()
            pdf.showPage()
            page_number += 1
            row_counter = 0

            # En la nueva página, dibujamos header y cabecera de tabla
            draw_header()
            y_position = draw_table_header(height - 100)

        # Fondo de la fila
        pdf.setFillColorRGB(*styles['row_color'])
        pdf.rect(40, y_position - row_height, width - 80, row_height, fill=1)

        # Contenido de la fila
        pdf.setFont(styles['body']['font'], styles['body']['size'])
        pdf.setFillColorRGB(*styles['body']['color'])

        # Truncamos textos si son muy largos
        cliente = (venta.cliente[:18] + '...') if len(venta.cliente) > 18 else venta.cliente
        vendedor = (venta.vendedor.username[:10] + '...') if len(venta.vendedor.username) > 10 else venta.vendedor.username

        # Posiciones para cada columna (igual que en el encabezado)
        pdf.drawString(50, y_position - (row_height / 1.5), str(venta.id))
        pdf.drawString(100, y_position - (row_height / 1.5), cliente)
        pdf.drawString(250, y_position - (row_height / 1.5), vendedor)
        pdf.drawRightString(400, y_position - (row_height / 1.5), f"${venta.total:,.2f}")
        pdf.drawString(460, y_position - (row_height / 1.5), venta.fecha_creacion.strftime("%d/%m/%Y"))

        # Sumamos al total
        total_ventas += venta.total

        # Línea divisoria debajo de la fila
        pdf.setStrokeColorRGB(0.8, 0.8, 0.8)
        pdf.line(40, y_position - row_height, width - 40, y_position - row_height)

        # Movemos el cursor para la siguiente fila
        y_position -= row_height
        row_counter += 1

    # Revisar si hay espacio para el total general
    if y_position < (margin_bottom + 40):
        # No hay espacio, forzamos nueva página
        draw_footer()
        pdf.showPage()
        page_number += 1
        draw_header()
        y_position = height - 100

    # Dibujamos el total general
    pdf.setFillColorRGB(*styles['accent']['color'])
    total_text = f"TOTAL GENERAL: ${total_ventas:,.2f}"
    pdf.setFont(styles['header']['font'], 14)
    text_width = pdf.stringWidth(total_text, styles['header']['font'], 14)

    # Un poco más abajo para separar del último row
    y_position -= 40
    pdf.rect(width - 40 - (text_width + 20), y_position, text_width + 20, 30, fill=1)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.drawRightString(width - 40 - 10, y_position + 8, total_text)

    # Footer final y guardado
    draw_footer()
    pdf.save()
    return response


def test_generate_pdf():
    """
    Genera 800 'ventas' de prueba y llama a 'generate_pdf'
    para verificar cómo se ve el PDF con muchas filas.
    Guarda el resultado como 'test_ventas.pdf'.
    """
    # Simulamos la estructura de 'venta' con namedtuple
    Vendedor = namedtuple("Vendedor", ["username"])
    Venta = namedtuple("Venta", ["id", "cliente", "vendedor", "total", "fecha_creacion"])

    # Creamos un vendedor genérico de prueba
    dummy_vendedor = Vendedor(username="VendedorDummy")

    # Creamos 800 ventas falsas
    ventas = []
    for i in range(1, 801):
        venta = Venta(
            id=i,
            cliente=f"Cliente {i}",
            vendedor=dummy_vendedor,
            total=random.randint(1000, 100000),  # total aleatorio
            fecha_creacion=datetime.now()
        )
        ventas.append(venta)

    # Llamamos a generate_pdf con los 800 objetos
    response = generate_pdf(ventas)

    # Guardamos el contenido PDF en un archivo local para inspeccionarlo
    with open("test_ventas.pdf", "wb") as f:
        f.write(response.content)

    print("PDF de prueba generado con 800 filas: 'test_ventas.pdf'")

# Para ejecutar este test desde la línea de comandos:
if __name__ == "__main__":
    test_generate_pdf()
