from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.caja_view, name='caja_view'),
    path('000/', views.caja_abierta_view, name='caja_abierta'),
    path('nuevo-pedido/', views.nuevo_pedido_view, name='nuevo_pedido'),
    path('facturacion/', views.facturacion_view, name='facturacion'),
    path('abrir-caja/', views.abrir_caja, name='abrir_caja'),
    path('cerrar-caja/', views.cerrar_caja, name='cerrar_caja'),
    path('verificar-caja/', views.verificar_caja, name='verificar_caja'),
    path('registrar-movimiento/', views.registrar_movimiento, name='registrar_movimiento'),
    path('resumen-caja/', views.resumen_caja, name='resumen_caja'),
    path('generar-factura/', views.generar_factura, name='generar_factura'),
]
