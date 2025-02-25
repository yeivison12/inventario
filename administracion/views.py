import difflib
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Producto, Categoria, EmpresaNombre  
from django.db.models import Q
from .forms import NombreEmpresaForm, ProductoForm, MarcaForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['similar_terms'] = getattr(self, 'similar_terms', [])
        return context
    
class DetalleProductoView(LoginRequiredMixin,DetailView):
    model = Producto
    template_name = 'administracion/detalle_producto.html'
    context_object_name = 'producto'

class NuevoProductoView(AdminRequiredMixin,CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'administracion/editar_producto.html'
    success_url = reverse_lazy('lista_productos')
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)
    
class EditarProductoView(AdminRequiredMixin,UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'administracion/editar_producto.html'
    success_url = reverse_lazy('lista_productos')
    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        return super().form_valid(form)

class EliminarProductoView(AdminRequiredMixin,DeleteView):
    model = Producto
    template_name = 'administracion/eliminar_producto.html'
    success_url = reverse_lazy('lista_productos')


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