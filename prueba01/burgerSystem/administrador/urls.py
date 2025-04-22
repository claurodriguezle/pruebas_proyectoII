#from django.views.generic import TemplateView
from django.urls import path
from . import views

app_name = 'administrador'

urlpatterns = [
    path('',views.menu, name='menu'),  #Ruta para la ventana principal
    path('crear/', views.crear_persona, name='crear_persona'),
    path('editar/<int:id>/', views.editar_persona, name='editar_persona'),
    path('eliminar/<int:id>/', views.eliminar_persona, name='eliminar_persona'),
    path('listar/', views.listar_personas, name='listar_personas'),

    # PRODUCTOS
    # página principal de productos
    path('productos/', views.productos, name='productos'),

    # HTMX partials y endpoints
    path('producto/partials/listar/', views.listar_partial,   name='listar_partial'),
    path('producto/partials/crear/', views.crear_partial,    name='crear_partial'),
    path('producto/crear/htmx/', views.crear_htmx,       name='crear_htmx'),
    path('producto/partials/editar/<int:pk>/', views.editar_partial, name='editar_partial'),
    path('producto/editar/<int:pk>/htmx/', views.editar_htmx,    name='editar_htmx'),
    path('producto/eliminar/<int:pk>/', views.eliminar_htmx,  name='eliminar_htmx'),
]