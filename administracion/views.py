import difflib
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Producto, Categoria, EmpresaNombre,HistorialProducto
from django.db.models import Q
from .forms import NombreEmpresaForm, ProductoForm, MarcaForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
    def handle_no_permission(self):
        raise PermissionDenied("No tienes permisos para acceder a esta página.")
class ListaProductosView(LoginRequiredMixin,ListView):
    model = Producto
    paginate_by = 6
    template_name = 'administracion/lista_productos.html'
    context_object_name = 'productos'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('categoria')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(categoria__nombre__icontains=query) |
                Q(precio__icontains=query)
            )   
            # Si no hay resultados, buscamos sugerencias
            if not queryset.exists():
                # Obtener todos los nombres de productos y categorías para comparar
                all_terms = list(Producto.objects.values_list('nombre', flat=True)) + \
                            list(Categoria.objects.values_list('nombre', flat=True))
                
                # Encontrar términos similares
                similar_terms = difflib.get_close_matches(query, all_terms, n=3, cutoff=0.6)
                self.similar_terms = similar_terms  # Guardar sugerencias en el contexto
            else:
                self.similar_terms = []  # No hay sugerencias si hay resultados

        return queryset.order_by('-fecha_creacion')
    historial =HistorialProducto.objects.all()
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['historial'] = HistorialProducto.objects.all()
        context['similar_terms'] = getattr(self, 'similar_terms', [])
        return context

class DetalleProductoView(LoginRequiredMixin,DetailView):
    model = Producto
    template_name = 'administracion/detalle_producto.html'
    context_object_name = 'producto'

class NuevoProductoView(AdminRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'administracion/editar_producto.html'
    success_url = reverse_lazy('lista_productos')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        form.instance.actualizado_por = self.request.user
        response = super().form_valid(form)
        # self.object es el producto creado
        HistorialProducto.objects.create(
            producto=self.object,
            nombre_producto=self.object.nombre,  # Se asigna el nombre del producto
            usuario=self.request.user,
            tipo_cambio="Creado",
            detalle_cambio="Producto creado en el sistema.",
            imagen_producto=self.object.imagen  # Guardamos la imagen actual
        )
        return response


class EditarProductoView(AdminRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'administracion/editar_producto.html'
    success_url = reverse_lazy('lista_productos')

    def form_valid(self, form):
        # Obtenemos el producto original antes de guardar
        producto_original = self.get_object()
        old_image = producto_original.imagen
        old_image_url = old_image.url if old_image else None

        # Preparamos el objeto nuevo, pero aún no lo guardamos en la BD
        nuevo_producto = form.save(commit=False)
        nuevo_producto.actualizado_por = self.request.user

        # Guardamos el producto primero, para que la nueva imagen se suba y tenga URL
        nuevo_producto.save()
        
        # Si usas form.changed_data, guárdalo antes de un nuevo form.save()
        changed_fields = form.changed_data  
        
        # Ahora sí podemos obtener la URL de la nueva imagen
        new_image = nuevo_producto.imagen
        new_image_url = new_image.url if new_image else None
        nombre_producto = self.object.nombre
        # Empezamos a armar la lista de cambios
        cambios = []
        
        for field in changed_fields:
            valor_antiguo = getattr(producto_original, field)
            valor_nuevo = getattr(nuevo_producto, field)
            nombre_producto=nombre_producto
            # 1. Si cambió la cantidad
            if field == "cantidad":
                diferencia = valor_nuevo - valor_antiguo
                if diferencia > 0:
                    cambios.append(
                        f"Cantidad aumentó en {diferencia} (de {valor_antiguo} a {valor_nuevo})"
                    )
                else:
                    cambios.append(
                        f"Cantidad reducida en {abs(diferencia)} (de {valor_antiguo} a {valor_nuevo})"
                    )

      
            elif field == "imagen":
                
                if old_image_url and new_image_url:
                    cambios.append(
                        f"Imagen: "
                        f"<img src='{old_image_url}' style='max-width:100px; vertical-align:middle;'> "
                        f"→ "
                        f"<img src='{new_image_url}' style='max-width:100px; vertical-align:middle;'>"
                    )
                elif old_image_url and not new_image_url:
                    cambios.append(
                        f"Imagen eliminada: "
                        f"<img src='{old_image_url}' style='max-width:100px; vertical-align:middle;'>"
                    )
                elif new_image_url and not old_image_url:
                    cambios.append(
                        f"Imagen agregada: "
                        f"<img src='{new_image_url}' style='max-width:100px; vertical-align:middle;'>"
                    )
                else:
                
                    cambios.append("Sin cambios en la imagen.")
            
           
            elif field == 'nombre':
                cambios.append(
                    f"Se cambió el {field} de: <strong>{valor_antiguo}</strong> a: <strong>{valor_nuevo}</strong>"
                )
            
            # 4. Otros campos
            else:
                cambios.append(f"{field}: {valor_antiguo} → {valor_nuevo}")


        if cambios:
            HistorialProducto.objects.create(
                producto=nuevo_producto,
                usuario=self.request.user,
                tipo_cambio="Editado",
                nombre_producto = nombre_producto,
                detalle_cambio="\n".join(cambios)
            )

        return super().form_valid(form)


class EliminarProductoView(AdminRequiredMixin, DeleteView):
    model = Producto
    template_name = 'administracion/eliminar_producto.html'
    success_url = reverse_lazy('lista_productos')

class ListaHistorialProductoView(AdminRequiredMixin, ListView):
    model = HistorialProducto
    template_name = 'administracion/historial_productos.html'
    context_object_name = 'historial'
    paginate_by = 10

    def get_queryset(self):
        queryset = HistorialProducto.objects.select_related("producto", "usuario").order_by("-fecha_cambio")

        # Obtener valores de los filtros
        producto_id = self.request.GET.get("producto_id")
        query = self.request.GET.get("q")

        # Filtrar por ID de producto (select)
        if producto_id:
            try:
                producto = Producto.objects.get(pk=producto_id)
                queryset = queryset.filter(
                    Q(producto_id=producto_id) | Q(nombre_producto=producto.nombre)
                )
            except Producto.DoesNotExist:
                queryset = queryset.none()

        # Filtrar por nombre del producto (buscador)
        if query:
            queryset = queryset.filter(nombre_producto__icontains=query)

            # Si no hay resultados, buscar términos similares
            if not queryset.exists():
                all_terms = list(HistorialProducto.objects.values_list('nombre_producto', flat=True))
                similar_terms = difflib.get_close_matches(query, all_terms, n=3, cutoff=0.6)
                self.similar_terms = similar_terms
            else:
                self.similar_terms = []
        else:
            self.similar_terms = []

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = Producto.objects.all()  # Lista para el select
        context['similar_terms'] = getattr(self, 'similar_terms', [])  # Sugerencias de búsqueda
        return context

########################################################################################

class ListarMarcas(AdminRequiredMixin,ListView):
    model = Categoria
    paginate_by = 6
    template_name = 'administracion/lista_marca.html'
    context_object_name = 'marcas'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
            )   
            # Si no hay resultados, buscamos sugerencias
            if not queryset.exists():
                # Obtener todos los nombres de categorías para comparar
                all_terms = list(Categoria.objects.values_list('nombre', flat=True))
                
                # Encontrar términos similares
                similar_terms = difflib.get_close_matches(query, all_terms, n=3, cutoff=0.6)
                self.similar_terms = similar_terms  # Guardar sugerencias en el contexto
            else:
                self.similar_terms = []  # No hay sugerencias si hay resultados

        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['similar_terms'] = getattr(self, 'similar_terms', [])
        return context

class EditarMarcaView(AdminRequiredMixin,UpdateView):
    model = Categoria
    form_class = MarcaForm
    template_name = 'administracion/crear_marca.html'
    success_url = reverse_lazy('lista_marcas')

    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)


class EliminarMarcaView(AdminRequiredMixin,DeleteView):
    model = Categoria
    template_name = 'administracion/eliminar_marca.html'
    success_url = reverse_lazy('lista_marcas')
    
class NuevaMarcaView(AdminRequiredMixin,CreateView):
    model = Categoria
    form_class = MarcaForm
    template_name = 'administracion/crear_marca.html'
    success_url = reverse_lazy('lista_marcas')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)
    
class DetalleMarcasView(AdminRequiredMixin,DetailView):
    model = Categoria
    template_name = 'administracion/detalle_marca.html'
    context_object_name = 'marcas'



class EmpresaNombreEditar(AdminRequiredMixin, UpdateView):
    model = EmpresaNombre
    form_class = NombreEmpresaForm
    template_name = 'administracion/nombre_empresa.html'
    
    def get_object(self, queryset=None):
        return EmpresaNombre.objects.first()
    
    def get_success_url(self):
        return str(reverse_lazy('lista_productos')) + '?empresaedit'
