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

    # APIs de estado de mesas — AJAX
    path('api/mesa/<int:mesa_id>/estado/', views.api_mesa_estado,        name='api_mesa_estado'),
    path('api/todas-mesas/estado/',        views.api_todas_mesas_estado, name='api_todas_mesas_estado'),

    # Egresos — AJAX
    path('egreso/',             views.registrar_egreso,         name='registrar_egreso'),

    # Reportes
    path('reporte/',            views.reporte_caja,             name='reporte_caja'),
]