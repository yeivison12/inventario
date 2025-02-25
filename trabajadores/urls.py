from django.urls import path

from .views import VentaListView, VentaDetailView, crear_venta, generar_ticket_venta, ExportVentasPDF,validar_ventas



urlpatterns = [
    path('', VentaListView.as_view(), name='venta_list'),
    path('<int:pk>/', VentaDetailView.as_view(), name='venta_detail'),
    path('<int:pk>/pdf/', generar_ticket_venta, name='venta_pdf'),
    path('crear/', crear_venta, name='venta_create'),
    path('export/pdf/', ExportVentasPDF.as_view(), name='venta_export_pdf'),
    path('validar/', validar_ventas, name='validar_ventas'), 
]

