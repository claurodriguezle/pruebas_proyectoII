from django.urls import path
from .import views

app_name = 'usuarios'

urlpatterns = [
    path('usuarios/', views.index, name='index'),
    path('usuarios/registro/', views.registro_cliente, name='registro'),
    path('usuarios/sesion/', views.iniciar_sesion, name='sesion'),
]