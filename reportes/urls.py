from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('ventas/productos/', views.reporte_ventas_productos, name='ventas_productos'),
    path('ventas/productos/datos/', views.reporte_ventas_productos_datos, name='ventas_productos_datos'),

    # Reportes Delivery VS Retiro
    path('pedidos/entregas/', views.reporte_entregas, name='entregas'),
    path('pedidos/entregas/datos/', views.reporte_entregas_datos, name='entregas_datos'),

    # REPORTE TOP 10 CLIENTES
    path('clientes/top/', views.reporte_top_clientes, name='top_clientes'),
    path('clientes/top/datos/', views.reporte_top_clientes_datos, name='top_clientes_datos'),

    # REPORTE DE VENTAS
    path('ventas/', views.reporte_ventas, name='ventas'),
    path('ventas/datos/', views.reporte_ventas_datos, name='ventas_datos'),
]