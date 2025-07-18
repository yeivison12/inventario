
from administracion.models import EmpresaNombre

def empresa(request):
    # Da el nombre de la empresa para el contexto global, revisa en settings.py en la sección de context_processors
    empresa = EmpresaNombre.objects.first()
    return {'empresa': empresa}
