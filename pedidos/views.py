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
from .services import validar_delivery
from usuarios.forms import DireccionForm
from django.views.decorators.http import require_http_methods
from django.utils import timezone


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
        #Probando
        print("ITEM CARRITO:", item)  # ← agregá esta línea
        producto = Producto.objects.get(pk=item['producto'])
        #Probando
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
def seleccionar_direccion_delivery(request):
    try:
        cliente = request.user.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró un cliente asociado.")
        return redirect('pedidos:menu_productos')
    
    direcciones = Direccion.objects.filter(cliente=cliente)

    # Opcion 1: Cliente elige una direccion existente

    if request.method == 'POST' and 'direccion_id' in request.POST:
        direccion_id = request.POST.get('direccion_id')
        try:
            direccion = Direccion.objects.get(pk=direccion_id)
        except Direccion.DoesNotExist:
            messages.error(request, "La direccion seleccionada no es valida.")
            return redirect('pedidos:seleccionar_direccion_delivery')
        
        resultado = validar_delivery(direccion)

        if not resultado['disponible']:
            messages.error(request, resultado['mensaje'])
            return redirect('pedidos:seleccionar_direccion_delivery')

        # Guarda en sesion y redirigi al resumen

        request.session['tipo_entrega'] = 'DE'
        request.session['direccion'] = direccion_id
        request.session['costo_delivery'] = resultado['costo_delivery']
        request.session['distancia_km'] = resultado['distancia_km']
        return redirect('pedidos:resumen_pedido')

    # 
    if request.method == 'POST' and 'nueva_direccion' in request.POST:
        form = DireccionForm(request.POST)
        if form.is_valid():
            nueva_direccion = form.save(commit=False)
            nueva_direccion.cliente = cliente
            nueva_direccion.save()

            resultado = validar_delivery(nueva_direccion)

            if not resultado['disponible']:
                # La guardamos pero avisamos que no hay delivery
                messages.error(request, resultado['mensaje'])
                return redirect('pedidos:seleccionar_direccion_delivery')

            request.session['tipo_entrega'] = 'DE'
            request.session['direccion'] = nueva_direccion.id
            request.session['costo_delivery'] = resultado['costo_delivery']
            request.session['distancia_km'] = resultado['distancia_km']
            return redirect('pedidos:resumen_pedido')
    else:
        form = DireccionForm()

    return render(request, 'pedidos/seleccionar_direccion_delivery.html', {
        'direcciones': direcciones,
        'form': form,
    })
    
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

    tipo_entrega = request.session.get('tipo_entrega')
    hora_estimada = request.session.get('hora_retiro')  
    direccion_id = request.session.get('direccion') 
    costo_delivery = request.session.get('costo_delivery', 0)
    distancia_km = request.session.get('distancia_km', None)

    # Recuperamos objeto direccion si es delivery
    direccion_obj = None
    if tipo_entrega == 'DE' and direccion_id:
        try:
            direccion_obj = Direccion.objects.get(
                pk=direccion_id, cliente=cliente
            )
        except Direccion.DoesNotExist:
            pass

    # Calcular total productos
    total_productos = sum(item['subtotal'] for item in carrito)

    total = total_productos + (costo_delivery if tipo_entrega == 'DE' else 0)

    context = {
        'carrito': carrito,
        'total_productos': total_productos,
        'total': total,
        'tipo_entrega': tipo_entrega,
        'hora_estimada': hora_estimada,
        'direccion': direccion_obj,
        'costo_delivery': costo_delivery,
        'distancia_km':distancia_km,
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
    costo_delivery = request.session.get('costo_delivery', 0)

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
                costo_delivery=costo_delivery,
                estado_cocina='PE',
                estado_entrega='PE',
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

                #Probando
                ingredientes_eliminados = item.get('sin', [])
                print("SIN INGREDIENTES:", ingredientes_eliminados) 
                for nombre_ing in ingredientes_eliminados:
                    print("Buscando ingrediente:", nombre_ing, "en producto:", producto.id)  
                    try:
                        ingrediente_obj = IngredienteProducto.objects.get(
                            producto=producto,
                            item__nombre__iexact=nombre_ing
                        )
                        print("Encontrado:", ingrediente_obj)  
                        IngredienteEliminadoPedido.objects.create(
                            detalle_pedido=detalle,
                            ingrediente=ingrediente_obj
                        )
                    except IngredienteProducto.DoesNotExist:
                        print("NO ENCONTRADO:", nombre_ing) 
                
                '''
                ingredientes_eliminados = item.get('sin', [])
                for ing_id in ingredientes_eliminados:
                    ingrediente_obj = IngredienteProducto.objects.get(pk=ing_id)
                    IngredienteEliminadoPedido.objects.create(
                        detalle_pedido=detalle,
                        ingrediente=ingrediente_obj
                    )
                '''
            # Si llega acá, todo fue bien, se hace commit automático
    except Exception as e:
        messages.error(request, f"Error al guardar el pedido: {e}")
        return redirect('pedidos:resumen_pedido')

    # Limpiar sesión solo si todo salió bien
    for key in ['carrito', 'tipo_entrega', 'hora_retiro', 'direccion', 'costo_delivery', 'distancia_km']:
        if key in request.session:
            del request.session[key]

    messages.success(request, "Pedido confirmado y guardado con éxito.")
    return redirect('pedidos:mis_pedidos')

@login_required
def mis_pedidos(request):
    try:
        cliente = request.user.cliente
    except:
        messages.error(request, "No tenés un perfil de cliente asociado.")
        return redirect('pedidos:menu_productos')

    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-id')

    for pedido in pedidos:
        try:
            pedido.factura_cliente = pedido.factura_pedido
        except:
            pedido.factura_cliente = None

    return render(request, 'pedidos/estado_pedido.html', {'pedidos': pedidos})


'''
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
'''
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
#CANCELAR EL PEDIDO CUANDO SE ENCUENTRA EN PENDIENTE UNA VEZ ENTRA EN PREPARACION YA NO SE PUEDE CANCELAR
@login_required
@require_http_methods(['POST'])
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=request.user.cliente)

    # Solo se puede cancelar si cocina aún no empezó
    if pedido.estado_cocina == 'PE':
        pedido.estado_entrega = 'CA'
        pedido.save(update_fields=['estado_entrega'])
        messages.success(request, "Tu pedido fue cancelado correctamente.")
    else:
        messages.error(request, "No podés cancelar este pedido, ya está en preparación.")

    return redirect('pedidos:mis_pedidos')
#Orden de pedidos
#Empleado/Cajero
def _get_filtros(request):
    return {
        'estado_activo': request.GET.get('estado', 'all'),
        'tipo_entrega':  request.GET.get('entrega', ''),
        'q':             request.GET.get('q', ''),
    }


def _enriquecer(pedido):
    """Agrega atributos calculados al pedido para usarlos en el template."""
    ahora = timezone.now()
    diff  = ahora - pedido.fecha
    pedido.minutos_transcurridos = int(diff.total_seconds() // 60)

    labels = {'PE': 'Marcar entregado', 'EN': 'Facturar'}
    pedido.btn_label = labels.get(pedido.estado_entrega, '')

    # Nombre del cliente para mostrar en la tabla
    persona = pedido.cliente.persona
    pedido.cliente_nombre = f"{persona.nombre} {persona.apellido}"

    return pedido


def _get_pedidos_empleado(filtros):
    qs = (
        Pedido.objects
        .select_related('cliente__persona')
        .prefetch_related('detalle__producto', 'detalle__adicionales__adicional', 'detalle__ingredientes_eliminados__ingrediente')
        .exclude(estado_entrega__in=['FA', 'CA'])
        .order_by('fecha')
    )

    if filtros['estado_activo'] != 'all':
        qs = qs.filter(estado_entrega=filtros['estado_activo'])

    if filtros['tipo_entrega']:
        qs = qs.filter(tipo_entrega=filtros['tipo_entrega'])

    if filtros['q']:
        qs = qs.filter(
            cliente__persona__nombre__icontains=filtros['q']
        ) | qs.filter(
            cliente__persona__apellido__icontains=filtros['q']
        )

    return [_enriquecer(p) for p in qs]


def _chips(filtros):
    base = Pedido.objects.exclude(estado_entrega__in=['FA', 'CA'])
    return {
        'cnt_all':       base.count(),
        'cnt_pendiente': base.filter(estado_entrega='PE').count(),
        'cnt_entregado': base.filter(estado_entrega='EN').count(),
        'cnt_listos':    base.filter(estado_cocina='LI', estado_entrega='PE').count(),
    }


# Vistas

@login_required
def panel_empleado(request):
    filtros = _get_filtros(request)
    pedidos = _get_pedidos_empleado(filtros)
    return render(request, 'orden_pedidos/panel_empleado.html', {
        **filtros, **_chips(filtros), 'pedidos': pedidos,
    })


@login_required
def empleado_tabla(request):
    filtros = _get_filtros(request)
    pedidos = _get_pedidos_empleado(filtros)
    return render(request, 'orden_pedidos/partials/empleado_tabla.html', {
        **filtros, **_chips(filtros), 'pedidos': pedidos,
    })


@login_required
def empleado_modal(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects
        .select_related('cliente__persona')
        .prefetch_related('detalle__producto', 'detalle__adicionales__adicional', 'detalle__ingredientes_eliminados__ingrediente'),
        pk=pedido_id
    )
    _enriquecer(pedido)
    return render(request, 'orden_pedidos/partials/empleado_modal.html', {'pedido': pedido})


@login_required
@require_http_methods(['POST'])
def empleado_avanzar(request, pedido_id):
    from facturacion.services import generar_factura_desde_pedido

    pedido    = get_object_or_404(Pedido, pk=pedido_id)
    siguiente = pedido.siguiente_estado_entrega

    if siguiente:
        pedido.estado_entrega = siguiente
        pedido.save(update_fields=['estado_entrega'])

        # ── Generar factura al marcar Entregado ──────────────────────────────
        if siguiente == 'EN':
            factura = generar_factura_desde_pedido(pedido)
            if factura:
                # Avanzar automáticamente a Facturado
                pedido.estado_entrega = 'FA'
                pedido.save(update_fields=['estado_entrega'])

    filtros = _get_filtros(request)
    pedidos = _get_pedidos_empleado(filtros)
    return render(request, 'orden_pedidos/partials/empleado_tabla.html', {
        **filtros, **_chips(filtros), 'pedidos': pedidos,
    })


@login_required
@require_http_methods(['POST'])
def empleado_actualizar(request, pedido_id):
    pedido        = get_object_or_404(Pedido, pk=pedido_id)
    nuevo_entrega = request.POST.get('estado_entrega', pedido.estado_entrega)

    if nuevo_entrega in ['PE', 'EN', 'FA', 'CA']:
        pedido.estado_entrega = nuevo_entrega
        pedido.save(update_fields=['estado_entrega'])

    filtros = _get_filtros(request)
    pedidos = _get_pedidos_empleado(filtros)
    return render(request, 'orden_pedidos/partials/empleado_tabla.html', {
        **filtros, **_chips(filtros), 'pedidos': pedidos,
    })

#COCINA

def _enriquecer_cocina(pedido):
    """Agrega atributos calculados al pedido para el panel de cocina."""
    from django.utils import timezone
    ahora = timezone.now()
    diff  = ahora - pedido.fecha
    pedido.minutos_transcurridos = int(diff.total_seconds() // 60)

    labels = {'PE': 'Iniciar preparación', 'EP': 'Marcar listo'}
    pedido.btn_label = labels.get(pedido.estado_cocina, '')

    persona = pedido.cliente.persona
    pedido.cliente_nombre = f"{persona.nombre} {persona.apellido}"

    return pedido


def _get_pedidos_cocina():
    """Devuelve solo los pedidos que cocina debe ver: PE y EP. Los LI se ocultan cuando ya fueron entregados."""
    from .models import Pedido
    qs = (
        Pedido.objects
        .select_related('cliente__persona')
        .prefetch_related('detalle__producto', 'detalle__adicionales__adicional', 'detalle__ingredientes_eliminados__ingrediente')
        .exclude(estado_cocina='LI', estado_entrega='EN')   # ya entregados, fuera
        .exclude(estado_cocina='LI', estado_entrega='FA')   # ya facturados, fuera
        .exclude(estado_entrega='CA')                        # cancelados, fuera
        .filter(estado_cocina__in=['PE', 'EP', 'LI'])        # solo los relevantes
        .order_by('fecha')                                   # más antiguos primero
    )
    return [_enriquecer_cocina(p) for p in qs]


# Vistas cocina

@login_required
def cocina_view(request):
    """Pantalla principal del panel de cocina."""
    pedidos = _get_pedidos_cocina()
    return render(request, 'orden_pedidos/cocina.html', {
        'pedidos':     pedidos,
        'cnt_pe':      sum(1 for p in pedidos if p.estado_cocina == 'PE'),
        'cnt_ep':      sum(1 for p in pedidos if p.estado_cocina == 'EP'),
        'cnt_li':      sum(1 for p in pedidos if p.estado_cocina == 'LI'),
    })


@login_required
def cocina_cards(request):
    """Fragmento de tarjetas — htmx lo recarga cada 5s."""
    pedidos = _get_pedidos_cocina()
    return render(request, 'orden_pedidos/partials/cocina_cards.html', {
        'pedidos': pedidos,
        'cnt_pe':  sum(1 for p in pedidos if p.estado_cocina == 'PE'),
        'cnt_ep':  sum(1 for p in pedidos if p.estado_cocina == 'EP'),
        'cnt_li':  sum(1 for p in pedidos if p.estado_cocina == 'LI'),
    })


@login_required
@require_http_methods(['POST'])
def cocina_avanzar(request, pedido_id):
    """Avanza el estado de cocina al siguiente: PE→EP→LI."""
    from .models import Pedido
    pedido    = get_object_or_404(Pedido, pk=pedido_id)
    siguiente = pedido.siguiente_estado_cocina   # propiedad del modelo
    if siguiente:
        pedido.estado_cocina = siguiente
        pedido.save(update_fields=['estado_cocina'])

    # Devuelve las tarjetas actualizadas
    pedidos = _get_pedidos_cocina()
    return render(request, 'orden_pedidos/partials/cocina_cards.html', {
        'pedidos': pedidos,
        'cnt_pe':  sum(1 for p in pedidos if p.estado_cocina == 'PE'),
        'cnt_ep':  sum(1 for p in pedidos if p.estado_cocina == 'EP'),
        'cnt_li':  sum(1 for p in pedidos if p.estado_cocina == 'LI'),
    })

#Coneccion con Facturacion
@login_required
def mi_factura(request, pedido_id):
    from facturacion.models import Factura
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=request.user.cliente)
    factura = get_object_or_404(
        Factura.objects
        .select_related('timbrado')
        .prefetch_related('detalles__producto'),
        pedido=pedido
    )
    return render(request, 'pedidos/mi_factura.html', {'factura': factura, 'pedido': pedido})


@login_required
@require_http_methods(['POST'])
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id, cliente=request.user.cliente)
    if pedido.estado_cocina == 'PE':
        pedido.estado_entrega = 'CA'
        pedido.save(update_fields=['estado_entrega'])
        messages.success(request, "Tu pedido fue cancelado correctamente.")
    else:
        messages.error(request, "No podés cancelar este pedido, ya está en preparación.")
    return redirect('pedidos:mis_pedidos')