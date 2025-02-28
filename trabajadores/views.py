import datetime
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Min, Max, Sum
import difflib
from reportlab.lib.pagesizes import letter
from django.utils.dateparse import parse_date
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import localtime
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from administracion.models import Categoria, EmpresaNombre
from .models import  Venta, VentaProducto, Producto
from .forms import VentaForm, VentaProductoForm
from datetime import datetime


# Vista para listar ventas
class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'trabajadores/venta_lista.html'
    context_object_name = 'ventas'
    paginate_by = 5
    ordering = ['-fecha_creacion']

    def get_queryset(self):
        user = self.request.user
        # Filtrar ventas según el usuario o superusuario
        queryset = Venta.objects.all() if user.is_superuser else Venta.objects.filter(vendedor=user)

        query = self.request.GET.get('q')
        if query:
            # Filtrar por cliente usando la consulta
            queryset = queryset.filter(Q(cliente__icontains=query))
            
            # Si no hay resultados, buscar términos similares
            if not queryset.exists():
                all_terms = list(Venta.objects.values_list('cliente', flat=True))
                self.similar_terms = difflib.get_close_matches(query, all_terms, n=3, cutoff=0.6)
            else:
                self.similar_terms = []
        
        return queryset.order_by('-fecha_creacion')
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Diccionario: clave = id de la venta, valor = lista de detalles (productos) de la venta
        context['ventas_productos'] = {
            venta.id: list(venta.ventaproducto_set.all()) for venta in context['ventas']
        }
        context['similar_terms'] = getattr(self, 'similar_terms', [])
        context['vendedores'] = User.objects.filter(id__in=Venta.objects.values_list('vendedor', flat=True).distinct())
        context['productos'] = Producto.objects.all()

        return context



# Vista para ver detalles de una venta
class VentaDetailView(LoginRequiredMixin,DetailView):
    model = Venta
    template_name = 'trabajadores/venta_detalle.html'
    context_object_name = 'venta'
@login_required   
def generar_ticket_venta(request, pk):
    venta = Venta.objects.get(pk=pk)
    empresa = EmpresaNombre.objects.first() 
    num_products = venta.ventaproducto_set.count()
    def format_price(price):
        # Convertimos el precio a float para trabajar con él
        price = float(price)
        # Si el precio no tiene parte decimal (es entero)
        if price % 1 == 0:
            # Lo mostramos como entero con separadores de miles
            return f"${int(price):,}"
        else:
            # Lo mostramos con dos decimales y separadores de miles
            return f"${price:,.2f}"
    # Cálculo dinámico de altura
    altura_fija = 85  # Altura base en mm (elementos fijos)
    altura_por_producto = 5  # Altura por producto en mm
    sum_deltas = (altura_fija + altura_por_producto * num_products) * mm
    ticket_height = sum_deltas + 10 * mm  # Margen superior adicional
    ticket_width = 80 * mm

    response = HttpResponse(content_type='application/pdf')
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
        pdf.drawCentredString(ticket_width / 2, y, f"NIT: N/A")
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

    # Productos
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
# Vista para crear una nueva venta
@login_required
def crear_venta(request):
    VentaProductoFormSet = inlineformset_factory(
        Venta, VentaProducto, form=VentaProductoForm, extra=0, can_delete=False
    )

    if request.method == "POST":
        venta_form = VentaForm(request.POST)
        formset = VentaProductoFormSet(request.POST)

        if venta_form.is_valid() and formset.is_valid():
            venta = venta_form.save(commit=False)
            venta.vendedor = request.user
            venta.creado_por = request.user
            venta.actualizado_por = request.user
            venta.save()

            formset.instance = venta
            formset.save()

            # Actualiza el total de la venta
            venta.actualizar_total()

            return redirect('venta_list')
    else:
        venta_form = VentaForm()
        formset = VentaProductoFormSet()

    # BÚSQUEDA
    query = request.GET.get('q', '')
    from_suggestion = request.GET.get('from_suggestion')
    if query:
        productos_list = Producto.objects.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query) |
            Q(categoria__nombre__icontains=query) |
            Q(precio__icontains=query)
        )
        # Si se hizo clic en una sugerencia, no mostramos el recuadro de sugerencias
        if from_suggestion:
            similar_terms = []
        else:
            # Si no hay resultados, buscamos sugerencias
            if not productos_list.exists():
                all_terms = list(Producto.objects.values_list('nombre', flat=True)) + \
                            list(Categoria.objects.values_list('nombre', flat=True))
                similar_terms = difflib.get_close_matches(query, all_terms, n=3, cutoff=0.6)
            else:
                similar_terms = []
    else:
        productos_list = Producto.objects.all()
        similar_terms = []

    # PAGINACIÓN
    paginator = Paginator(productos_list, 5)  # 5 productos por página
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    context = {
        'form': venta_form,
        'formset': formset,
        'productos': productos,
        'query': query,                # Para mantener el valor ingresado en el buscador
        'similar_terms': similar_terms # Sugerencias basadas en la búsqueda
    }

    return render(request, 'trabajadores/venta_form.html', context)

class ExportVentasPDF(UserPassesTestMixin, View):
    """Genera un PDF con la lista de ventas filtradas."""
    
    def test_func(self):
        """Restringe el acceso solo a usuarios con is_staff=True"""
        return self.request.user.is_staff

    def get_queryset(self):
        """Obtiene y filtra el queryset según los parámetros."""
        user = self.request.user
        queryset = Venta.objects.all() if user.is_superuser else Venta.objects.filter(vendedor=user)
        
        # Si es el formulario de "Ventas del Día"
        if not self.request.GET.get('fecha_inicio') and not self.request.GET.get('fecha_fin'):
            from datetime import date
            today = date.today()
            queryset = queryset.filter(fecha_creacion__date=today)
        else:
            # Si es el formulario de "Ventas por Rango de Fechas"
            fecha_inicio = self.request.GET.get('fecha_inicio')
            fecha_fin = self.request.GET.get('fecha_fin')
            if fecha_inicio:
                fecha_inicio = parse_date(fecha_inicio)
                if fecha_inicio:
                    queryset = queryset.filter(fecha_creacion__date__gte=fecha_inicio)
            if fecha_fin:
                fecha_fin = parse_date(fecha_fin)
                if fecha_fin:
                    queryset = queryset.filter(fecha_creacion__date__lte=fecha_fin)
        
        # Filtrado por vendedor
        vendedor_id = self.request.GET.get('vendedor')
        if vendedor_id:
            queryset = queryset.filter(vendedor_id=vendedor_id)
        
        # Filtrado por producto (a través de la relación VentaProducto)
        producto_id = self.request.GET.get('producto')
        if producto_id:
            queryset = queryset.filter(ventaproducto_set__producto_id=producto_id).distinct()
        
        # Filtrado por método de pago
        metodo_pago = self.request.GET.get('metodo_pago')
        if metodo_pago:
            queryset = queryset.filter(metodo_pago=metodo_pago)
        
        return queryset.select_related('vendedor')
    def generate_pdf(self, queryset):
        """Genera un PDF con la lista de ventas filtradas de manera profesional y eficiente."""
        
        # Configuración inicial del PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="ventas.pdf"'

        pdf = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        page_number = 1

        # Configuración de dimensiones
        row_height = 25
        margin_bottom = 80
        line_height = 15

        # Estilos centralizados
        styles = {
            'title': {'font': 'Helvetica-Bold', 'size': 18, 'color': (0.2, 0.4, 0.6)},
            'header': {'font': 'Helvetica-Bold', 'size': 12, 'color': (1, 1, 1)},
            'body': {'font': 'Helvetica', 'size': 10, 'color': (0.2, 0.2, 0.2)},
            'accent': {'color': (0.2, 0.4, 0.6)},
            'row_color': (0.95, 0.95, 0.95),
            'footer_font': {'font': 'Helvetica', 'size': 8, 'color': (0.4, 0.4, 0.4)}
        }

        # Obtener el rango de fechas del queryset
        min_date = queryset.aggregate(min_date=Min('fecha_creacion'))['min_date']
        max_date = queryset.aggregate(max_date=Max('fecha_creacion'))['max_date']
        date_range = (min_date.strftime("%d/%m/%Y") if min_date.date() == max_date.date() 
                    else f"{min_date.strftime('%d/%m/%Y')} al {max_date.strftime('%d/%m/%Y')}")

        # Funciones auxiliares
        def truncate_text(text, max_length):
            """Trunca el texto si excede la longitud máxima, añadiendo '...'."""
            return text[:max_length - 3] + '...' if len(text) > max_length else text
        
        def format_price(price):
            price = float(price)
            if price % 1 == 0:
                return f"${int(price):,}"
            else:
                return f"${price:,.2f}"
        
        def draw_header():
            """Dibuja el encabezado del PDF."""
            y = height - 50
            pdf.setFont(styles['title']['font'], styles['title']['size'])
            pdf.setFillColorRGB(*styles['title']['color'])
            pdf.drawString(40, y, f"Reporte de Ventas Detallado para {date_range}")
            y -= 20
            pdf.setFont(styles['body']['font'], styles['body']['size'])
            pdf.setFillColorRGB(*styles['body']['color'])
            pdf.drawString(40, y, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            y -= 10
            pdf.line(40, y, width - 40, y)
            return y - 15

        def draw_footer():
            empresa = EmpresaNombre.objects.first()
            """Dibuja el pie de página del PDF."""
            pdf.setFont(styles['footer_font']['font'], styles['footer_font']['size'])
            pdf.setFillColorRGB(*styles['footer_font']['color'])
            if empresa.nombre:
                pdf.drawCentredString(width / 2, 30, f"Página {page_number} - Sistema de Inventario {empresa.nombre}")
            else:
                pdf.drawCentredString(width / 2, 30, f"Página {page_number} - Sistema de Inventario ")
            pdf.line(40, 40, width - 40, 40)

        def draw_table_header(y):
            """Dibuja el encabezado de la tabla."""
            pdf.setFillColorRGB(*styles['accent']['color'])
            pdf.rect(40, y - row_height, width - 80, row_height, fill=1)
            pdf.setFont(styles['header']['font'], styles['header']['size'])
            pdf.setFillColorRGB(*styles['header']['color'])
            headers = ["ID", "Cliente", "Vendedor", "Productos", "Pago", "Total", "Fecha"]
            x_positions = [50, 100, 170, 250, 350, 425, 510]
            for i, header in enumerate(headers):
                pdf.drawString(x_positions[i], y - (row_height / 1.5), header)
            return y - row_height

        # Inicio del contenido
        y_position = draw_table_header(draw_header())
        total_ventas = 0

        # Optimizar la consulta con prefetch_related
        for venta in queryset.prefetch_related('ventaproducto_set__producto'):
            productos_vendidos = venta.ventaproducto_set.all()
            productos_lista = [
                    f"{vp.cantidad}x {vp.nombre_producto if vp.nombre_producto else 'Producto eliminado'}"
                    for vp in productos_vendidos]

            num_productos = len(productos_lista)
            row_height_adjusted = row_height + (num_productos - 1) * line_height

            # Verificar espacio suficiente o iniciar nueva página
            if y_position < margin_bottom + row_height_adjusted:
                draw_footer()
                pdf.showPage()
                page_number += 1
                y_position = draw_table_header(draw_header())

            # Dibujar fila de la venta
            pdf.setFillColorRGB(*styles['row_color'])
            pdf.rect(40, y_position - row_height_adjusted, width - 80, row_height_adjusted, fill=1)
            pdf.setFont(styles['body']['font'], styles['body']['size'])
            pdf.setFillColorRGB(*styles['body']['color'])

            pdf.drawString(50, y_position - 15, str(venta.id))
            pdf.drawString(100, y_position - 15, truncate_text(str(venta.cliente), 18))
            pdf.drawString(170, y_position - 15, truncate_text(venta.vendedor.username, 10))
            pdf.drawString(350, y_position - 15, truncate_text(str(venta.metodo_pago), 10))
            pdf.drawRightString(460, y_position - 15, format_price(venta.total))
            
            pdf.drawString(490, y_position - 15, localtime(venta.fecha_creacion).strftime("%d/%m/%Y %H:%M"))

            # Dibujar lista de productos
            for i, product in enumerate(productos_lista):
                pdf.drawString(250, y_position - 13 - i * line_height, truncate_text(product, 16))

            total_ventas += venta.total
            pdf.line(40, y_position - row_height_adjusted, width - 40, y_position - row_height_adjusted)
            y_position -= row_height_adjusted

        # Asegurar espacio para el total general
        if y_position < margin_bottom + 40:
            draw_footer()
            pdf.showPage()
            page_number += 1
            y_position = draw_table_header(draw_header())

        # Dibujar total general
        pdf.setFont(styles['header']['font'], 14)
        total_text = f"TOTAL GENERAL: {format_price(total_ventas)}"
        text_width = pdf.stringWidth(total_text, styles['header']['font'], 14)
        y_position -= 40
        pdf.setFillColorRGB(*styles['accent']['color'])
        pdf.rect(width - 40 - (text_width + 20), y_position, text_width + 20, 30, fill=1)
        pdf.setFillColorRGB(1, 1, 1)
        pdf.drawRightString(width - 40 - 10, y_position + 8, total_text)

        # Finalizar el PDF
        draw_footer()
        pdf.save()
        return response
        
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
         
        # Validar si hay registros en el rango de fechas
        if not queryset.exists():
            # Crear contexto manualmente para el error
            context = {
                'error_message': "No hay registros de ventas en el rango de fechas seleccionado.",
                'vendedores': User.objects.filter(groups__name='Trabajadores')  # Añadir vendedores aquí si es necesario
            }
            return render(request, "trabajadores/venta_lista.html", context)

        return self.generate_pdf(queryset)



def validar_ventas(request):
    """ Valida ventas según fechas, vendedor o producto. """

    # 📌 Obtener parámetros
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    vendedor_id = request.GET.get('vendedor')
    producto_id = request.GET.get('producto')
    metodo_pago = request.GET.get('metodo_pago') 


    queryset = Venta.objects.all()

    # ✅ Validación de fechas
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date() if fecha_inicio_str else None
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date() if fecha_fin_str else None
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido.'}, status=400)

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        return JsonResponse({'error': 'La fecha de inicio no puede ser posterior a la fecha fin.'}, status=400)

    if fecha_inicio:
        queryset = queryset.filter(fecha_creacion__date__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_creacion__date__lte=fecha_fin)

    # ✅ Validación del vendedor
    if vendedor_id and vendedor_id.isdigit():
        queryset = queryset.filter(vendedor_id=vendedor_id)

    # ✅ Validación del producto (Usar la relación correcta con VentaProducto)
    if producto_id and producto_id.isdigit():
        queryset = queryset.filter(ventaproducto_set__producto_id=producto_id)  # 🔥 Cambio importante
    if metodo_pago:
        queryset = queryset.filter(metodo_pago=metodo_pago)
    # ✅ Verificar si hay registros que cumplen con los filtros
    existe = queryset.exists()

    return JsonResponse({'existe': existe})
