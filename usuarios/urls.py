from django.urls import path
from .import views

app_name = 'usuarios'

urlpatterns = [
    path('usuarios/', views.index, name='index'),
    path('registro/', views.registro_cliente, name='registro'),
    path('sesion/', views.iniciar_sesion, name='sesion'),
    path('perfil/', views.perfil_user, name='perfil_user'),
    path('crear_direccion/', views.agregar_direccion, name='crear_direccion'),
    path('direciones/', views.listar_direcciones, name='listar_direc'),
    path('exit/', views.exit, name='exit'),
]