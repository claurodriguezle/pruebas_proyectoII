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
    path('producto/desactivar/<int:pk>/', views.desactivar_producto_htmx, name='desactivar_producto'),
    path('producto/activar/<int:pk>/', views.activar_producto_htmx, name='activar_producto'),


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
    path('categorias/toggle/<int:pk>/', views.toggle_categoria, name='toggle_categoria'),
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

    # RUTAS PARA SALARIOS
    path('salarios/',                  views.lista_salarios,   name='salarios'),
    path('salarios/crear/',            views.crear_salario,    name='crear_salario'),
    path('salarios/<int:pk>/editar/',  views.editar_salario,   name='editar_salario'),
    path('salarios/<int:pk>/eliminar/',views.eliminar_salario, name='eliminar_salario'),
    # ===== NUEVAS RUTAS HTMX PARA SALARIOS =====
    path('salarios/listar-partial/', views.listar_salarios_partial, name='listar_salarios_partial'),
    path('salarios/crear-partial/', views.crear_salario_partial, name='crear_salario_partial'),
    path('salarios/crear-htmx/', views.crear_salario_htmx, name='crear_salario_htmx'),
    path('salarios/editar-partial/<int:pk>/', views.editar_salario_partial, name='editar_salario_partial'),
    path('salarios/editar-htmx/<int:pk>/', views.editar_salario_htmx, name='editar_salario_htmx'),
    path('salarios/eliminar-htmx/<int:pk>/', views.eliminar_salario_htmx, name='eliminar_salario_htmx'),

    # RUTAS PARA TIPO DE EMPLEADO
    path('tipo-empleado/',                          views.lista_tipo_empleado,           name='lista_tipo_empleado'),
    path('tipo-empleado/rows/',                     views.tipo_empleado_listar_partial,  name='tipo_empleado_rows'),
    path('tipo-empleado/crear/partial/',            views.tipo_empleado_crear_partial,   name='tipo_empleado_crear_partial'),
    path('tipo-empleado/<int:pk>/editar/partial/',  views.tipo_empleado_editar_partial,  name='tipo_empleado_editar_partial'),
    path('tipo-empleado/crear/',                    views.tipo_empleado_crear_htmx,      name='tipo_empleado_crear_htmx'),
    path('tipo-empleado/<int:pk>/editar/',          views.tipo_empleado_editar_htmx,     name='tipo_empleado_editar_htmx'),
    path('tipo-empleado/<int:pk>/toggle/',          views.tipo_empleado_toggle_htmx,     name='tipo_empleado_toggle'),

    # MESAS
    path('mesas/', views.mesas, name='mesas'),
    path('mesas/partials/listar/', views.mesas_listar_partial, name='mesas_listar_partial'),
    path('mesas/partials/crear/', views.mesas_crear_partial, name='mesas_crear_partial'),
    path('mesas/crear/htmx/', views.mesas_crear_htmx, name='mesas_crear_htmx'),
    path('mesas/partials/editar/<int:pk>/', views.mesas_editar_partial, name='mesas_editar_partial'),
    path('mesas/editar/<int:pk>/htmx/', views.mesas_editar_htmx, name='mesas_editar_htmx'),
    path('mesas/eliminar/<int:pk>/', views.mesas_eliminar_htmx, name='mesas_eliminar_htmx'),

    #Localidades
    path('localidades/',                            views.localidades,                  name='localidades'),
 
    #Ciudades
    path('localidades/ciudades/listar/',            views.ciudades_listar_partial,      name='ciudades_listar_partial'),
    path('localidades/ciudades/crear/partial/',     views.ciudades_crear_partial,       name='ciudades_crear_partial'),
    path('localidades/ciudades/editar/<int:pk>/partial/', views.ciudades_editar_partial, name='ciudades_editar_partial'),
    path('localidades/ciudades/crear/',             views.ciudades_crear_htmx,          name='ciudades_crear_htmx'),
    path('localidades/ciudades/editar/<int:pk>/',   views.ciudades_editar_htmx,         name='ciudades_editar_htmx'),
    path('localidades/ciudades/toggle/<int:pk>/',   views.ciudades_toggle_htmx,         name='ciudades_toggle_htmx'),

    #Barrios
    path('localidades/barrios/listar/',             views.barrios_listar_partial,       name='barrios_listar_partial'),
    path('localidades/barrios/crear/partial/',      views.barrios_crear_partial,        name='barrios_crear_partial'),
    path('localidades/barrios/editar/<int:pk>/partial/', views.barrios_editar_partial,  name='barrios_editar_partial'),
    path('localidades/barrios/crear/',              views.barrios_crear_htmx,           name='barrios_crear_htmx'),
    path('localidades/barrios/editar/<int:pk>/',    views.barrios_editar_htmx,          name='barrios_editar_htmx'),
    path('localidades/barrios/toggle/<int:pk>/',    views.barrios_toggle_htmx,          name='barrios_toggle_htmx'),

    #Adicionales
    path('adicionales/', views.adicionales, name='adicionales'),
    path('adicionales/listar/', views.adicionales_listar_partial, name='adicionales_listar_partial'),
    path('adicionales/crear/partial/', views.adicionales_crear_partial, name='adicionales_crear_partial'),
    path('adicionales/crear/', views.adicionales_crear_htmx, name='adicionales_crear_htmx'),
    path('adicionales/editar/<int:pk>/partial/', views.adicionales_editar_partial, name='adicionales_editar_partial'),
    path('adicionales/editar/<int:pk>/', views.adicionales_editar_htmx, name='adicionales_editar_htmx'),
    path('adicionales/toggle/<int:pk>/', views.adicionales_toggle_htmx, name='adicionales_toggle_htmx'),
]