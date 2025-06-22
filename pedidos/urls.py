from django.urls import path
from .import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu_productos, name='menu_productos'),
    path('productos/lista/', views.lista_productos, name='lista_productos'),
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
    path('pedido/pedido-confirmado/', views.confirmacion_pedido, name='pedido_confirmado'),
    #Rutas para pruebas de orden de pedidos
    #Empleado/Cajero
    path('orden/', views.ordenes_view, name='ordenes_view'),
    #Cocina
    path('cocina/', views.cocina_view, name='cocina_view'),
]
