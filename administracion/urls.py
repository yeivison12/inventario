from django.urls import path
from django.conf.urls.static import static

from inventario import settings
from .views import ListaProductosView, DetalleProductoView,EmpresaNombre,EmpresaNombreEditar, NuevoProductoView, EditarProductoView, EliminarProductoView, ListarMarcas, EditarMarcaView, EliminarMarcaView, DetalleMarcasView,NuevaMarcaView

urlpatterns = [
    path('', ListaProductosView.as_view(), name='lista_productos'),
    path('producto/<int:pk>/', DetalleProductoView.as_view(), name='detalle_producto'),
    path('producto/nuevo/', NuevoProductoView.as_view(), name='nuevo_producto'),
    path('producto/<int:pk>/editar/', EditarProductoView.as_view(), name='editar_producto'),
    path('producto/<int:pk>/eliminar/', EliminarProductoView.as_view(), name='eliminar_producto'),
    
    path('marcas', ListarMarcas.as_view(), name='lista_marcas'),
    path('marcas/nueva/', NuevaMarcaView.as_view(), name='nueva_marca'),

   
    path('empresa/editar/', EmpresaNombreEditar.as_view(), name='empresa_editar'),

    path('marcas/<int:pk>/editar/', EditarMarcaView.as_view(), name='editar_marcas'),
    path('marcas/<int:pk>/eliminar/', EliminarMarcaView.as_view(), name='eliminar_marcas'),
    path('marcas/<int:pk>/', DetalleMarcasView.as_view(), name='detalle_marcas'),
]
if settings.DEBUG:urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
