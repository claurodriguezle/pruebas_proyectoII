from django.views.generic import TemplateView
from django.urls import path
from . import views

urlpatterns = [
    path('',views.menu, name='menu'),  #Ruta para la ventana principal
    path('crear/', views.crear_persona, name='crear_persona'),
    path('editar/<int:id>/', views.editar_persona, name='editar_persona'),
    path('eliminar/<int:id>/', views.eliminar_persona, name='eliminar_persona'),
    path('listar/', views.listar_personas, name='listar_personas'),

    #Rutas para compras
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/crear/', views.crear_compra, name='crear_compra'),
]