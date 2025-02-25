from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    CustomLoginView,
    custom_logout
)


urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='iniciar_sesion'),
    path('logout/', custom_logout, name='cerrar_sesion'),
]