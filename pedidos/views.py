from django.shortcuts import render, redirect, get_object_or_404
from administrador.models import Producto, CategoriaProducto, Cliente, IngredienteProducto, Direccion
from django.contrib.auth.decorators import login_required
from .models import Adicional, Pedido, DetallePedido, DetalleAdicionalPedido, IngredienteEliminadoPedido
from .forms import RetiroForm
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from datetime import datetime

def index(request):
    return render(request, 'pedidos/index.html')

def menu_productos(request):
    categorias = CategoriaProducto.objects.all()
    adicionales = Adicional.objects.all()
    carrito = request.session.get('carrito', [])
    
    # Total de item para el contador del carrito
    cantidad_carrito = sum(item['cantidad'] for item in carrito)

    return render(request, 'pedidos/menu_productos.html', {
        'categorias': categorias,
        'adicionales': adicionales,
        'cantidad_carrito': cantidad_carrito
        })

def lista_productos(request):
    categoria_nombre = request.GET.get('categoria')
    if categoria_nombre:
        productos = Producto.objects.filter(estado='A', categoria__nombre_categ=categoria_nombre)
    else:
        productos = Producto.objects.filter(estado='A')
    return render(request, 'pedidos/partials/productos_lista.html', {'productos': productos})

def contador_carrito(request):
    carrito = request.session.get('carrito', [])
    total = sum(item['cantidad'] for item in carrito)
    html = render_to_string('pedidos/partials/contador_carrito.html', {'cantidad': total})
    return HttpResponse(html)

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

    request.session['carrito'] = carrito
    return HttpResponse(status=204)

def carrito(request):
    carrito = request.session.get('carrito', [])

    # Calcular subtotal por producto y total general
    for item in carrito:
        total_adicionales = sum(a['precio'] for a in item['adicionales'])
        item['subtotal'] = (item['precio'] + total_adicionales) * item['cantidad']

    # Calculamos el total general
    total = sum(item['subtotal'] for item in carrito)

    # Total de item para el contador del carrito
    cantidad_carrito = sum(item['cantidad'] for item in carrito)

    return render(request, 'pedidos/carrito.html', {
            'carrito': carrito,
            'total': total,
            'cantidad_carrito': cantidad_carrito
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
        'total': total,
    }
    
    return render(request, 'pedidos/partials/contenido_carrito.html', context)

@login_required
def tipo_entrega(request):
    form = RetiroForm()
    return render(request, 'pedidos/tipo_entrega.html', {'form': form})

@login_required
def retiro_local(request):
    if request.method == 'POST':
        form = RetiroForm(request.POST)
        if form.is_valid():
            # Guardar los datos en la sesion
            request.session['tipo_entrega'] = form.cleaned_data['tipo_entrega']
            request.session['hora_retiro'] = form.cleaned_data['hora_retiro'].strftime('%H:%M')
            request.session['direccion'] = 'N/A'

            return redirect('pedidos:resumen_pedido')
    else:
        form = RetiroForm()
    return render(request, 'pedidos/tipo_entrega.html', {'form': form})

@login_required
def resumen_pedido(request):
    carrito = request.session.get('carrito', [])
    #Tomamos los datos del cliente para su facturacion
    cliente = request.user.cliente
    persona = cliente.persona
    documento_factura = persona.ruc if persona.ruc else persona.cedula


    if not carrito:
        # Redirige si el carrito está vacío
        return redirect('pedidos:menu_productos')

    # Simulamos tipo de entrega (esto luego se recupera desde POST o session)
    tipo_entrega = request.session.get('tipo_entrega')  # o 'delivery'
    hora_estimada = request.session.get('hora_retiro')  # Simulado
    direccion = request.session.get('direccion')  # Solo si es delivery

    # Calcular total
    total = sum(item['subtotal'] for item in carrito)

    context = {
        'carrito': carrito,
        'total': total,
        'tipo_entrega': tipo_entrega,
        'hora_estimada': hora_estimada,
        'direccion': direccion,
        #Datos de facturacion
        'persona': persona,
        'documento_factura' : documento_factura,
    }

    return render(request, 'pedidos/resumen_pedido.html', context)

@login_required
def confirmar_pedido(request):
    carrito = request.session.get('carrito', [])
    if not carrito:
        messages.error(request, "Tu carrito está vacío")
        return redirect('pedidos:menu_productos')

    tipo_entrega = request.session.get('tipo_entrega')
    hora_retiro_str = request.session.get('hora_retiro')
    direccion_id = request.session.get('direccion')

    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró un cliente asociado a tu usuario")
        return redirect('pedidos:menu_productos')
    
    direccion_obj = None
    if tipo_entrega == 'DE' and direccion_id:
        try:
            direccion_obj = Direccion.objects.get(pk=direccion_id, cliente=cliente)
        except Direccion.DoesNotExist:
            messages.error(request, "La dirección seleccionada no es válida.")
            return redirect('pedidos:resumen_pedido')

    hora_retiro = None
    if hora_retiro_str:
        try:
            hora_retiro = datetime.strptime(hora_retiro_str, '%H:%M').time()
        except ValueError:
            hora_retiro = None

    total = sum(item['subtotal'] for item in carrito)

    try:
        with transaction.atomic():
            pedido = Pedido.objects.create(
                cliente=cliente,
                total=total,
                tipo_entrega=tipo_entrega,
                hora_retiro=hora_retiro,
                direccion_entrega=direccion_obj,
                estado='PE',
            )

            for item in carrito:
                producto = Producto.objects.get(pk=item['producto'])
                detalle = DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    nota=item.get('nota', '')
                )

                adicionales = item.get('adicionales', [])
                for ad in adicionales:
                    adicional_obj = Adicional.objects.get(pk=ad['id'])
                    DetalleAdicionalPedido.objects.create(
                        detalle_pedido=detalle,
                        adicional=adicional_obj,
                        cantidad=ad.get('cantidad', 1)
                    )

                ingredientes_eliminados = item.get('ingredientes_eliminados', [])
                for ing_id in ingredientes_eliminados:
                    ingrediente_obj = IngredienteProducto.objects.get(pk=ing_id)
                    IngredienteEliminadoPedido.objects.create(
                        detalle_pedido=detalle,
                        ingrediente=ingrediente_obj
                    )

            # Si llega acá, todo fue bien, se hace commit automático
    except Exception as e:
        messages.error(request, f"Error al guardar el pedido: {e}")
        return redirect('pedidos:resumen_pedido')

    # Limpiar sesión solo si todo salió bien
    for key in ['carrito', 'tipo_entrega', 'hora_retiro', 'direccion']:
        if key in request.session:
            del request.session[key]

    messages.success(request, "Pedido confirmado y guardado con éxito.")
    return redirect('pedidos:mis_pedidos')
    
def confirmacion_pedido(request):
    return render(request, 'pedidos/confirmacion_pedido.html')

@login_required
def mis_pedidos(request): # Muestra el estado e historial del pedido de CLIENTE

    # Aseguramos si el pedido pertenece al cliente logueado
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No tienes un perfil de cliente asociado.")
        return redirect('pedidos:menu_productos')

    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-id')

    context = {
        "pedidos": pedidos
    }

    return render(request, 'pedidos/estado_pedido.html', context)

@login_required
def detalle_mi_pedido(request, pedido_id):
    # Obtiene el pedido y nos asegura que sea del cliente loguedo
    pedido = get_object_or_404(
        Pedido,
        id=pedido_id,
        cliente = request.user.cliente
    )

    # Trae los detalles del pedido
    detalles= pedido.detalle.all().prefetch_related('adicionales')

    context = {
        'pedido': pedido,
        'detalles': detalles
    }

    return render(request, 'pedidos/detalle_mi_pedido.html', context)

#Orden de pedidos
#Empleado/Cajero
def ordenes_view(request):
    return render(request, 'orden_pedidos/orden.html')

#Cocina
def cocina_view(request):
    return render(request,'orden_pedidos/cocina.html')
