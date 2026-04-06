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
    path('factura/', views.facturas_list, name='facturas_list'),
    path('factura/<int:factura_id>/', views.factura_detalle, name='factura_detalle'),

    #Facturacion en Caja
    path('emitir/<int:venta_id>/', views.emitir_factura, name='emitir_factura'),
    path('buscar-cliente/', views.buscar_cliente_factura, name='buscar_cliente_factura'),
    path('cliente/crear-rapido/', views.crear_cliente_rapido, name='crear_cliente_rapido'),
]