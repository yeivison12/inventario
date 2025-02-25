
from administracion.models import EmpresaNombre

def empresa(request):
    # Obtiene la primera empresa o None si no existe
    empresa = EmpresaNombre.objects.first()
    return {'empresa': empresa}
