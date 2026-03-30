from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    # Apertura y Cierre
    path('apertura/', views.apertura_caja, name='apertura_caja'),
    path('cierre/', views.cierre_caja, name='cierre_caja'),

    # Punto de Venta (POS)
    path('pos/', views.punto_de_venta, name='punto_de_venta'),

    # AJAX endpoints
    path('pos/completar/', views.completar_venta, name='completar_venta'),
    path('pos/egreso/', views.registrar_egreso, name='registrar_egreso'),

    # Reportes
    path('reporte/', views.reporte_caja, name='reporte_caja'),
]