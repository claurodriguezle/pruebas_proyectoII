# facturacion/urls.py
from django.urls import path
from . import views

app_name = 'facturacion'

urlpatterns = [
    path('timbrado/', views.TimbradoListView.as_view(), name='timbrado_list'),
    path('timbrado/nuevo/', views.TimbradoCreateView.as_view(), name='timbrado_create'),
    path('timbrado/editar/<int:pk>/', views.TimbradoUpdateView.as_view(), name='timbrado_update'),
    path('timbrado/toggle-active/<int:pk>/', views.timbrado_toggle_active, name='timbrado_toggle_active'),
    path('timbrados/eliminar/<int:pk>/', views.timbrado_soft_delete, name='timbrado_soft_delete'),
    #Rutas para pruebas de Factura
    path('factura/factura_view/', views.factura_view, name='factura_view'),
]