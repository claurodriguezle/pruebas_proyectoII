from django.views.generic import TemplateView
from django.urls import path
from . import views


app_name = 'administrador'

urlpatterns = [
    path('',views.menu, name='menu'),  #Ruta para la ventana principal
    path('crear/', views.crear_persona, name='crear_persona'),
    path('editar/<int:id>/', views.editar_persona, name='editar_persona'),
    path('eliminar/<int:id>/', views.eliminar_persona, name='eliminar_persona'),
    path('listar/', views.listar_personas, name='listar_personas'),

    # PRODUCTOS
    # página principal de productos
    path('productos/', views.productos, name='productos'),

    # HTMX partials y endpoints
    path('producto/partials/listar/', views.listar_partial, name='listar_partial'),
    path('producto/partials/crear/', views.crear_partial, name='crear_partial'),
    path('producto/crear/htmx/', views.crear_htmx, name='crear_htmx'),
    path('producto/partials/editar/<int:pk>/', views.editar_partial, name='editar_partial'),
    path('producto/editar/<int:pk>/htmx/', views.editar_htmx, name='editar_htmx'),
    path('producto/eliminar/<int:pk>/', views.eliminar_htmx, name='eliminar_htmx'),


    #Rutas para compras
    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/crear/', views.crear_compra, name='crear_compra'),
    path('compras/<int:compra_id>/',views.detalle_compra, name='detalle_compra'),
    path('compras/editar/<int:compra_id>/', views.editar_compra, name='editar_compra'),
    path('compras/eliminar/<int:compra_id>/', views.eliminar_compra, name='eliminar_compra'),
    path('compras/<int:compra_id>/anular/', views.anular_compra, name='anular_compra'),


    #Rutas para stock
    path('stock/',views.lista_stock, name='lista_stock'),
    path('stock/crear/',views.crear_stock, name='crear_stock'),
    path('stock/editar/<int:stock_id>',views.editar_stock, name='editar_stock'),
    path('stock/eliminar/<int:stock_id>',views.eliminar_stock, name='eliminar_stock'),

    #Rutas para items
    path ('items/',views.lista_items, name='lista_items'),
    path('items/editar/<int:pk>/', views.editar_item, name='editar_item'),
    path('items/eliminar/<int:pk>/', views.eliminar_item, name='eliminar_item'),
    # CATEGORIAS
    path('categorias/', views.categorias, name='categorias'),
    path('categorias/crear', views.crear_categorias, name='crear_categorias'),
    path('categorias/listar', views.listar_categorias_partial, name="listar_categorias_partial"),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='editar_categoria'),

    # INGREDIENTES DE PRODUCTOS
    path('ingredientes/<int:id>/', views.ingredientes, name='ingredientes'),
    path('cargar-items/', views.cargar_items, name="cargar_items"),
    path('ingredientes/<int:producto_id>/agregar', views.agregar_ingredientes, name='agregar_ingredientes'),
    path('ingredientes/<int:producto_id>/listar/', views.listar_ingredientes, name='listar_ingredientes'),
    path('ingredientes/eliminar/<int:pk>/', views.eliminar_ingrediente, name='eliminar_ingrediente'),
    # INGREDIENTES EDITAR INLINE
    path('ingredientes/<int:pk>/editar-form/', views.editar_ingrediente_form, name='editar_ingrediente_form'),
    path('ingredientes/<int:pk>/actualizar/', views.actualizar_ingrediente, name='actualizar_ingrediente'),
    path('ingredientes/<int:pk>/ver/', views.ver_fila_ingrediente, name='ver_fila_ingrediente'),

]