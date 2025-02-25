from django.apps import AppConfig

class TrabajadoresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trabajadores'

    def ready(self):
        import trabajadores.signals
