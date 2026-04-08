from django.urls import path
from .import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu_productos, name='menu_productos'),
    path('productos/lista/', views.lista_productos, name='lista_productos'),
    path('buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('modal-personalizacion/<int:producto_id>/', views.modal_personalizacion, name='modal_personalizacion'),
    path('carrito/', views.carrito, name='carrito'),
    path('contador-carrito/', views.contador_carrito, name='contador_carrito'),
    path('agregar-al-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/incrementar/<int:item_index>/', views.incrementar_cantidad, name='incrementar_cantidad'),
    path('carrito/decrementar/<int:item_index>/', views.decrementar_cantidad, name='decrementar_cantidad'),
    path('carrito/eliminar/<int:item_index>/', views.eliminar_item, name='eliminar_item'),
    path('usuarios/tipo-entrega/', views.tipo_entrega, name='tipo_entrega'),
    path('retiro-local/', views.retiro_local, name='retiro_local'),
    path('resumen/', views.resumen_pedido, name='resumen_pedido'),
    path('pedido/confirmar-pedido/', views.confirmar_pedido, name='confirmar_pedido'),
    path('mis_pedidos', views.mis_pedidos, name='mis_pedidos'),
    path('mis-pedidos/partial/', views.mis_pedidos_partial, name='mis_pedidos_partial'),
    path('detalle_pedido/<int:pedido_id>/', views.detalle_mi_pedido, name="detalle_mi_pedido"),
    path('delivery/', views.seleccionar_direccion_delivery, name='seleccionar_direccion_delivery'),
    #RUTA PARA CANCELAR EL PEDIDO CUANDO SE ENCUENTRA EN PENDIENTE
    path('cancelar_pedido/<int:pedido_id>/', views.cancelar_pedido, name='cancelar_pedido'),


    #Rutas para pruebas de orden de pedidos
    # Panel del Empleado
    path('orden/', views.panel_empleado, name='ordenes_view'),
    path('orden/tabla/', views.empleado_tabla, name='empleado_tabla'),
    path('orden/modal/<int:pedido_id>/', views.empleado_modal, name='empleado_modal'),
    path('orden/avanzar/<int:pedido_id>/', views.empleado_avanzar, name='empleado_avanzar'),
    path('orden/actualizar/<int:pedido_id>/', views.empleado_actualizar, name='empleado_actualizar'),

    #  Panel de Cocina
    path('cocina/', views.cocina_view, name='cocina_view'),
    path('cocina/cards/', views.cocina_cards, name='cocina_cards'),
    path('cocina/avanzar/<int:pedido_id>/', views.cocina_avanzar, name='cocina_avanzar'),
    #Rutas para la Facturacion
    path('mi_factura/<int:pedido_id>/', views.mi_factura, name='mi_factura'),
]
