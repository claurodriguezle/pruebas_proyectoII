from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import uuid

def caja_view(request):
    """Vista principal de caja"""
    context = {
        'caja_abierta': request.session.get('caja_abierta', False),
        'caja_empleado': request.session.get('caja_empleado', ''),
        'caja_monto_inicial': request.session.get('caja_monto_inicial', 0),
        'caja_monto_actual': request.session.get('caja_monto', 0),
    }
    return render(request, 'caja/index.html', context)

def caja_abierta_view(request):
    """Vista de caja abierta"""
    if not request.session.get('caja_abierta', False):
        return redirect('caja:caja_view')
    
    # Calcular resumen
    monto_inicial = float(request.session.get('caja_monto_inicial', 0))
    movimientos = request.session.get('caja_movimientos', [])
    monto_actual = float(request.session.get('caja_monto', 0))
    
    ingresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'ingreso')
    egresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'egreso')
    ganancia_real = ingresos - egresos
    
    context = {
        'caja_empleado': request.session.get('caja_empleado', ''),
        'resumen': {
            'monto_inicial': monto_inicial,
            'ingresos': ingresos,
            'egresos': egresos,
            'monto_actual': monto_actual,
            'ganancia_real': ganancia_real,
        },
        'movimientos': movimientos
    }
    return render(request, 'caja/caja_abierta.html', context)

def nuevo_pedido_view(request):
    """Vista para crear nuevo pedido"""
    if not request.session.get('caja_abierta', False):
        return redirect('caja:caja_view')
    
    return render(request, 'caja/nuevo_pedido.html')

def facturacion_view(request):
    """Vista para facturación"""
    if not request.session.get('caja_abierta', False):
        return redirect('caja:caja_view')
    
    # Obtener el último pedido registrado
    ultimo_pedido = None
    movimientos = request.session.get('caja_movimientos', [])
    
    for movimiento in reversed(movimientos):
        if movimiento['tipo'] == 'ingreso' and 'pedido_data' in movimiento:
            ultimo_pedido = movimiento['pedido_data']
            break
    
    if not ultimo_pedido:
        return redirect('caja:nuevo_pedido')
    
    # Calcular subtotales para cada item
    for item in ultimo_pedido['items']:
        item['subtotal'] = item['precio'] * item['cantidad']
    
    # Generar número de factura y fecha
    numero_factura = f"FAC-{uuid.uuid4().hex[:8].upper()}"
    fecha_actual = timezone.now().strftime('%d/%m/%Y')
    hora_actual = timezone.now().strftime('%H:%M:%S')
    
    # Traducir tipo de entrega
    tipo_entrega = {
        'local': 'Consumo en Local',
        'takeaway': 'Para Llevar',
        'delivery': 'Delivery'
    }.get(ultimo_pedido['tipoEntrega'], ultimo_pedido['tipoEntrega'])
    
    context = {
        'pedido_actual': ultimo_pedido,
        'numero_factura': numero_factura,
        'fecha_actual': fecha_actual,
        'hora_actual': hora_actual,
        'tipo_entrega': tipo_entrega,
        'caja_empleado': request.session.get('caja_empleado', '')
    }
    
    return render(request, 'caja/facturacion.html', context)

@require_http_methods(["POST"])
@csrf_exempt
def generar_factura(request):
    """Generar factura"""
    try:
        if not request.session.get('caja_abierta', False):
            return JsonResponse({'success': False, 'message': 'La caja no está abierta'})
        
        data = json.loads(request.body)
        
        # Obtener el último pedido registrado
        ultimo_pedido = None
        movimientos = request.session.get('caja_movimientos', [])
        
        for movimiento in reversed(movimientos):
            if movimiento['tipo'] == 'ingreso' and 'pedido_data' in movimiento:
                ultimo_pedido = movimiento['pedido_data']
                movimiento_id = movimientos.index(movimiento)
                break
        
        if not ultimo_pedido:
            return JsonResponse({'success': False, 'message': 'No hay pedido para facturar'})
        
        # Generar número de factura y fecha
        numero_factura = f"FAC-{uuid.uuid4().hex[:8].upper()}"
        fecha_actual = timezone.now().strftime('%d/%m/%Y')
        hora_actual = timezone.now().strftime('%H:%M:%S')
        
        # Crear factura
        factura = {
            'numero': numero_factura,
            'fecha': fecha_actual,
            'hora': hora_actual,
            'cliente': data['cliente'],
            'pedido': ultimo_pedido,
            'observaciones': data.get('observaciones', ''),
            'empleado': request.session.get('caja_empleado', ''),
            'total': ultimo_pedido['total']
        }
        
        # Guardar factura en sesión
        facturas = request.session.get('facturas', [])
        facturas.append(factura)
        request.session['facturas'] = facturas
        
        # Actualizar movimiento con datos de factura
        movimientos[movimiento_id]['factura'] = numero_factura
        request.session['caja_movimientos'] = movimientos
        
        return JsonResponse({
            'success': True, 
            'message': 'Factura generada exitosamente',
            'factura': factura
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})

@require_http_methods(["POST"])
@csrf_exempt
def abrir_caja(request):
    """Abrir caja del día"""
    try:
        data = json.loads(request.body)
        empleado = data.get('empleado', '').strip()
        monto_inicial = float(data.get('monto_inicial', 0))
        
        if not empleado:
            return JsonResponse({'success': False, 'message': 'El nombre del empleado es requerido'})
        
        if monto_inicial < 0:
            return JsonResponse({'success': False, 'message': 'El monto inicial no puede ser negativo'})
        
        # Inicializar sesión de caja
        request.session['caja_abierta'] = True
        request.session['caja_empleado'] = empleado
        request.session['caja_monto'] = monto_inicial
        request.session['caja_monto_inicial'] = monto_inicial
        request.session['caja_movimientos'] = []
        request.session['caja_fecha_apertura'] = timezone.now().isoformat()
        request.session['facturas'] = []
        
        return JsonResponse({'success': True, 'message': 'Caja abierta exitosamente'})
        
    except ValueError as e:
        return JsonResponse({'success': False, 'message': 'Monto inicial inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})

@require_http_methods(["POST"])
@csrf_exempt
def cerrar_caja(request):
    """Cerrar caja del día"""
    try:
        if not request.session.get('caja_abierta', False):
            return JsonResponse({'success': False, 'message': 'La caja no está abierta'})
        
        # Guardar datos de cierre
        request.session['caja_abierta'] = False
        request.session['caja_fecha_cierre'] = timezone.now().isoformat()
        
        return JsonResponse({'success': True, 'message': 'Caja cerrada exitosamente'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})

@require_http_methods(["POST"])
@csrf_exempt
def registrar_movimiento(request):
    """Registrar movimiento de caja"""
    try:
        if not request.session.get('caja_abierta', False):
            return JsonResponse({'success': False, 'message': 'La caja no está abierta'})
        
        data = json.loads(request.body)
        tipo = data.get('tipo', '').lower()
        concepto = data.get('concepto', '').strip()
        monto = float(data.get('monto', 0))
        
        if tipo not in ['ingreso', 'egreso']:
            return JsonResponse({'success': False, 'message': 'Tipo de movimiento inválido'})
        
        if not concepto:
            return JsonResponse({'success': False, 'message': 'El concepto es requerido'})
        
        if monto <= 0:
            return JsonResponse({'success': False, 'message': 'El monto debe ser mayor a cero'})
        
        # Crear movimiento
        movimientos = request.session.get('caja_movimientos', [])
        nuevo_movimiento = {
            'hora': timezone.now().strftime('%H:%M:%S'),
            'tipo': tipo,
            'concepto': concepto,
            'monto': monto,
            'responsable': request.session.get('caja_empleado', 'Empleado'),
            'fecha': timezone.now().strftime('%Y-%m-%d')
        }
        
        # Agregar datos del pedido si existen
        if 'pedido_data' in data:
            nuevo_movimiento['pedido_data'] = data['pedido_data']
        
        movimientos.append(nuevo_movimiento)
        request.session['caja_movimientos'] = movimientos
        
        # Actualizar monto en caja
        monto_actual = float(request.session.get('caja_monto', 0))
        if tipo == 'ingreso':
            monto_actual += monto
        else:
            monto_actual -= monto
        
        request.session['caja_monto'] = monto_actual
        
        return JsonResponse({
            'success': True, 
            'message': 'Movimiento registrado exitosamente',
            'movimiento': nuevo_movimiento,
            'monto_actual': monto_actual
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'message': 'Monto inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})

@csrf_exempt
def verificar_caja(request):
    """Verificar estado de caja"""
    try:
        caja_abierta = request.session.get('caja_abierta', False)
        movimientos = request.session.get('caja_movimientos', [])
        
        return JsonResponse({
            'success': True,
            'abierta': caja_abierta,
            'empleado': request.session.get('caja_empleado', ''),
            'monto_actual': request.session.get('caja_monto', 0),
            'movimientos': movimientos
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})

@csrf_exempt
def resumen_caja(request):
    """Obtener resumen de caja"""
    try:
        if not request.session.get('caja_abierta', False):
            return JsonResponse({'success': False, 'message': 'La caja no está abierta'})
        
        monto_inicial = float(request.session.get('caja_monto_inicial', 0))
        movimientos = request.session.get('caja_movimientos', [])
        monto_actual = float(request.session.get('caja_monto', 0))
        
        ingresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'ingreso')
        egresos = sum(float(m['monto']) for m in movimientos if m['tipo'] == 'egreso')
        ganancia_real = ingresos - egresos
        
        return JsonResponse({
            'success': True,
            'resumen': {
                'monto_inicial': monto_inicial,
                'ingresos': ingresos,
                'egresos': egresos,
                'monto_actual': monto_actual,
                'ganancia_real': ganancia_real,
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error interno: {str(e)}'})
