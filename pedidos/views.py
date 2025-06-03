from django.shortcuts import render, redirect, get_object_or_404
from administrador.models import Producto, CategoriaProducto
from .models import Adicional

def index(request):
    return render(request, 'pedidos/index.html')

def menu_productos(request):
    categorias = CategoriaProducto.objects.all()
    adicionales = Adicional.objects.all()
    return render(request, 'pedidos/menu_productos.html', {
        'categorias': categorias,
        'adicionales': adicionales,
        })

def lista_productos(request):
    categoria_nombre = request.GET.get('categoria')
    if categoria_nombre:
        productos = Producto.objects.filter(estado='A', categoria__nombre_categ=categoria_nombre)
    else:
        productos = Producto.objects.filter(estado='A')
    return render(request, 'pedidos/partials/productos_lista.html', {'productos': productos})

def agregar_al_carrito(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        adicionales_ids = request.POST.getlist('adicional[]', [])
        sin = request.POST.getlist('sin[]', [])
        comentario = request.POST.get('comentarios', '').strip().lower()

        producto = get_object_or_404(Producto, id=producto_id)
        adicionales = Adicional.objects.filter(id__in=adicionales_ids)

        # Normalizamos listas para comparacion
        adicionales_ids_sorted = sorted([str(a.id) for a in adicionales])
        sin_sorted = sorted(sin)

        # Estructura básica del carrito en sesión
        carrito = request.session.get('carrito', [])

        # Verificamos si ya existe el mismo item
        item_encontrado = False
        for item in carrito:
            if (
                item['producto'] == producto.id and 
                sorted([str(a['id']) for a in item['adicionales']]) == adicionales_ids_sorted and
                sorted(item['sin']) == sin_sorted and
                item['comentario'].strip().lower() == comentario
            ):
                # Ya existe, sumamos cantidad
                item['cantidad'] += 1
                item_encontrado = True
                break
        
        if not item_encontrado:
            # Agregamos el producto con sus detalles
            nuevo_item = {
                'producto': producto.id,
                'nombre': producto.nombre,
                'precio': producto.precio,
                'imagen': producto.imagen.url if producto.imagen else '',
                'personalizable': True if sin or adicionales_ids or comentario else False,
                'adicionales': [
                    {'id': a.id, 'nombre': a.nombre, 'precio': a.precio}
                    for a in adicionales
                ],
                'sin': sin,
                'comentario': comentario,
                'cantidad': 1,
                'subtotal': producto.precio + sum(a.precio for a in adicionales) # calculamos subtotal inicial
            }
            carrito.append(nuevo_item)

        request.session['carrito'] = carrito

        return redirect('pedidos:carrito') # ir a la vista de carrito
    return redirect('pedidos:menu_productos')

def carrito(request):
    carrito = request.session.get('carrito', [])

    # Calcular subtotal por producto y total general
    for item in carrito:
        total_adicionales = sum(a['precio'] for a in item['adicionales'])
        item['subtotal'] = (item['precio'] + total_adicionales) * item['cantidad']

    # Calculamos el total general
    total = sum(item['subtotal'] for item in carrito)

    return render(request, 'pedidos/carrito.html', {
            'carrito': carrito,
            'total': total
        })
    
def _calcular_totales_y_actualizar_sesion(request, carrito):
    # Recalcular subtotal de cada item
    for item in carrito:
        total_adicionales = sum(a['precio'] for a in item['adicionales'])
        item['subtotal'] = (item['precio'] + total_adicionales) * item['cantidad']
    
    # Total general
    total = sum(item['subtotal'] for item in carrito)

    # Actualizar la sesion
    request.session['carrito'] = carrito
    return total

def incrementar_cantidad(request, item_index):
    carrito = request.session.get('carrito', [])

    if 0 <= item_index < len(carrito) and carrito[item_index]['cantidad'] < 10:
        carrito[item_index]['cantidad'] += 1
    
    total = _calcular_totales_y_actualizar_sesion(request, carrito)

    context = {
        'carrito': carrito,
        'total': total,
    }
    return render(request, 'pedidos/partials/contenido_carrito.html', context)

def decrementar_cantidad(request, item_index):
    carrito = request.session.get('carrito', [])
    if 0 <= item_index < len(carrito) and carrito[item_index]['cantidad'] > 1:
        carrito[item_index]['cantidad'] -= 1
    
    total = _calcular_totales_y_actualizar_sesion(request, carrito)


    context = {
        'carrito': carrito,
        'total': total,
    
    }

    return render(request, 'pedidos/partials/contenido_carrito.html', context)

def eliminar_item(request, item_index):
    carrito = request.session.get('carrito', [])
    if 0 <= item_index < len(carrito):
        carrito.pop(item_index)
    total = _calcular_totales_y_actualizar_sesion(request, carrito)

    if not carrito:
        return render (request, 'pedidos/partials/carrito_vacio.html')
    
    context = {
        'carrito': carrito,
        'total': total
    }
    
    return render(request, 'pedidos/partials/contenido_carrito.html', context)

#Orden de pedidos
#Empleado/Cajero
def ordenes_view(request):
    return render(request, 'orden_pedidos/orden.html')

#Cocina
def cocina_view(request):
    return render(request,'orden_pedidos/cocina.html')
