from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    # Punto de Venta (POS)
    path('pos/', views.punto_de_venta, name='punto_de_venta'),
    path('pos/agregar/', views.agregar_producto_venta, name='agregar_producto'),
    path('pos/completar/', views.completar_venta, name='completar_venta'),
    
    # Apertura y Cierre de Caja
    path('apertura/', views.apertura_caja, name='apertura_caja'),
    path('cierre/', views.cierre_caja, name='cierre_caja'),
    
    # Reportes
    path('reporte/', views.reporte_caja, name='reporte_caja'),
]