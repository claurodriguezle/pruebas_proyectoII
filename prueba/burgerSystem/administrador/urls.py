from django.urls import path
from . import views

urlpatterns = [
    path('',views.menu, name='menu'),  #Ruta para la ventana principal
    path("registro/", views.crear_cliente, name="registro"),
    path('listar/', views.listar, name="listar"),
    path('clientes/crear',views.crear_cliente, name="crear_cliente"),
    path('cliente/editar/<int:id>/', views.editar_cliente, name="editar_cliente"),
    path('clientes/eliminar/<int:id>', views.eliminar_cliente,name="eliminar_cliente"),
]