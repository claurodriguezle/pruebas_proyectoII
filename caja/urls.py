from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    # Apertura y Cierre
    path('apertura/',           views.apertura_caja,            name='apertura_caja'),
    path('cierre/',             views.cierre_caja,              name='cierre_caja'),

    # Punto de Venta
    path('pos/',                views.punto_de_venta,           name='punto_de_venta'),

    # Operaciones de mesa/cuenta — AJAX
    path('mesa/abrir/',         views.abrir_cuenta,             name='abrir_cuenta'),
    path('mesa/pedido/',        views.agregar_pedido_cuenta,    name='agregar_pedido_cuenta'),
    path('mesa/cuenta/<int:cuenta_id>/', views.ver_cuenta,      name='ver_cuenta'),
    path('mesa/cobrar/',        views.cobrar_cuenta,            name='cobrar_cuenta'),
    path('pos/cancelar-pedido/<int:pedido_id>/', views.pos_cancelar_pedido, name='pos_cancelar_pedido'),

    # APIs de estado de mesas — AJAX
    path('api/mesa/<int:mesa_id>/estado/', views.api_mesa_estado,        name='api_mesa_estado'),
    path('api/todas-mesas/estado/',        views.api_todas_mesas_estado, name='api_todas_mesas_estado'),

    # API para pedidos pendientes — AJAX
    path('api/pedidos-pendientes/', views.api_pedidos_pendientes, name='api_pedidos_pendientes'),
    path('facturar-pedido/<int:pedido_id>/', views.facturar_desde_caja, name='facturar_desde_caja'),
]