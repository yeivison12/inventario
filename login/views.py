from pyexpat.errors import messages
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from administracion.models import EmpresaNombre

# Create your views here.
class CustomLoginView(LoginView):
    template_name = 'login/login.html'  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nombre"] = EmpresaNombre.objects.all()
        return context
    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy('lista_productos') + '?login'
        
        # Verificar si el usuario pertenece al grupo "Trabajadores"
        if user.groups.filter(name='Trabajadores').exists():
            return reverse_lazy('venta_list') + '?login'
        
        return reverse_lazy('lista_productos') + '?login'
    
def custom_logout(request):
    logout(request)  # Cierra la sesión del usuario
    return redirect('/?logout') 