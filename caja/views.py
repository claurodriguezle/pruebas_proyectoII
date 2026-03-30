from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
from decimal import Decimal
import json

# ============================================================================
# DATOS DE PRUEBA (MOCK DATA) - Para probar sin modelos
# ============================================================================

PRODUCTOS_MOCK = [
    {'id': 1, 'nombre': 'Hamburguesa Clásica', 'precio_venta': 8.50, 'stock': 100, 'activo': True},
    {'id': 2, 'nombre': 'Hamburguesa con Queso', 'precio_venta': 9.50, 'stock': 100, 'activo': True},
    {'id': 3, 'nombre': 'Hamburguesa Bacon', 'precio_venta': 10.50, 'stock': 100, 'activo': True},
    {'id': 4, 'nombre': 'Papas Fritas', 'precio_venta': 4.00, 'stock': 150, 'activo': True},
    {'id': 5, 'nombre': 'Gaseosa', 'precio_venta': 2.50, 'stock': 200, 'activo': True},
    {'id': 6, 'nombre': 'Malteada', 'precio_venta': 5.00, 'stock': 80, 'activo': True},
]

CLIENTES_MOCK = [
    {'id': 1, 'nombre': 'Cliente Frecuente', 'telefono': '0981234567'},
    {'id': 2, 'nombre': 'Cliente VIP', 'telefono': '0987654321'},
    {'id': 3, 'nombre': 'Juan Pérez', 'telefono': '0981112233'},
]

CAJA_MOCK = {
    'id': 1,
    'fecha_apertura': datetime.now(),
    'usuario_apertura': {'username': 'empleado1'},
    'monto_inicial': Decimal('100.00'),
    'monto_final_esperado': Decimal('600.00'),
    'estado': 'abierta',
}

# ============================================================================
# VISTAS
# ============================================================================

@login_required
def punto_de_venta(request):
    """Vista principal del POS - Con datos mock"""
    # En producción: verificar si hay caja abierta en BD
    # Por ahora usamos datos mock
    
    context = {
        'caja': CAJA_MOCK,
        'productos': PRODUCTOS_MOCK,
        'clientes': CLIENTES_MOCK,
    }
    return render(request, 'caja/punto_de_venta.html', context)

#@login_required
def agregar_producto_venta(request):
    """Agregar producto a la venta (AJAX) - Versión mock"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto_id = int(data.get('producto_id'))
            cantidad = int(data.get('cantidad', 1))
            
            # Buscar producto en mock data
            producto = next((p for p in PRODUCTOS_MOCK if p['id'] == producto_id), None)
            
            if not producto:
                return JsonResponse({'success': False, 'error': 'Producto no encontrado'})
            
            # Guardar en sesión la venta actual
            if 'venta_actual' not in request.session:
                request.session['venta_actual'] = {
                    'productos': [],
                    'total': 0
                }
            
            # Verificar si el producto ya está en la venta
            producto_en_venta = False
            for item in request.session['venta_actual']['productos']:
                if item['producto_id'] == producto_id:
                    item['cantidad'] += cantidad
                    item['subtotal'] = item['precio'] * item['cantidad']
                    producto_en_venta = True
                    break
            
            if not producto_en_venta:
                request.session['venta_actual']['productos'].append({
                    'producto_id': producto['id'],
                    'nombre': producto['nombre'],
                    'precio': float(producto['precio_venta']),
                    'cantidad': cantidad,
                    'subtotal': float(producto['precio_venta'] * cantidad)
                })
            
            # Recalcular total
            request.session['venta_actual']['total'] = sum(
                item['subtotal'] for item in request.session['venta_actual']['productos']
            )
            
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'venta': request.session['venta_actual']
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def completar_venta(request):
    """Completar la venta - Versión mock (simula guardado)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            venta_actual = request.session.get('venta_actual')
            
            if not venta_actual or not venta_actual['productos']:
                return JsonResponse({'success': False, 'error': 'No hay productos en la venta'})
            
            monto_recibido = float(data.get('monto_recibido', 0))
            total_venta = venta_actual['total']
            
            if monto_recibido < total_venta:
                return JsonResponse({
                    'success': False, 
                    'error': f'Monto insuficiente. Total: ${total_venta:.2f}'
                })
            
            vuelto = monto_recibido - total_venta
            
            # En producción: aquí se guardan los datos en BD
            # Por ahora solo simulamos el éxito
            
            pedido_id = 1000 + int(datetime.now().timestamp()) % 10000
            
            # Limpiar sesión
            del request.session['venta_actual']
            request.session.modified = True
            
            return JsonResponse({
                'success': True,
                'pedido_id': pedido_id,
                'venta_id': pedido_id,
                'vuelto': vuelto,
                'total': total_venta,
                'monto_recibido': monto_recibido
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def apertura_caja(request):
    """Apertura de caja - Versión mock"""
    if request.method == 'POST':
        monto_inicial = request.POST.get('monto_inicial')
        
        # En producción: crear Caja en BD
        # Por ahora solo redirigimos al POS
        
        return redirect('caja:punto_de_venta')
    
    return render(request, 'caja/apertura_caja.html')

@login_required
def cierre_caja(request):
    """Cierre de caja - Versión mock"""
    # Datos mock para probar el template
    caja = CAJA_MOCK.copy()
    caja['monto_final_esperado'] = Decimal('600.00')
    
    totales = {
        'ventas': Decimal('500.00'),
        'egresos': Decimal('0.00'),
        'ganancia': Decimal('500.00'),
    }
    
    if request.method == 'POST':
        monto_final_real = request.POST.get('monto_final_real')
        observaciones = request.POST.get('observaciones')
        
        diferencia = float(monto_final_real) - float(caja['monto_final_esperado'])
        
        # En producción: guardar cierre en BD
        # Por ahora mostramos el resumen
        
        return render(request, 'caja/resumen_cierre.html', {
            'caja': caja,
            'totales': totales,
            'diferencia': diferencia,
        })
    
    context = {
        'caja': caja,
        'totales': totales,
        'movimientos': [],  # En producción: caja.movimientos.all()
    }
    return render(request, 'caja/cierre_caja.html', context)

@login_required
def reporte_caja(request):
    """Reporte de cajas - Versión mock"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Datos mock para probar el template
    cajas_mock = [
        {
            'id': 1,
            'fecha_apertura': datetime(2025, 5, 19, 8, 0),
            'fecha_cierre': datetime(2025, 5, 19, 20, 0),
            'usuario_apertura': {'username': 'empleado1'},
            'monto_inicial': Decimal('100.00'),
            'ventas': Decimal('500.00'),
            'egresos': Decimal('50.00'),
            'ganancia': Decimal('450.00'),
        },
        {
            'id': 2,
            'fecha_apertura': datetime(2025, 5, 18, 8, 0),
            'fecha_cierre': datetime(2025, 5, 18, 20, 0),
            'usuario_apertura': {'username': 'empleado2'},
            'monto_inicial': Decimal('100.00'),
            'ventas': Decimal('650.00'),
            'egresos': Decimal('30.00'),
            'ganancia': Decimal('620.00'),
        },
    ]
    
    totales = {
        'total_ventas': sum(c['ventas'] for c in cajas_mock),
        'total_egresos': sum(c['egresos'] for c in cajas_mock),
        'total_ganancias': sum(c['ganancia'] for c in cajas_mock),
    }
    
    context = {
        'cajas': cajas_mock,
        'total_ventas': totales['total_ventas'],
        'total_egresos': totales['total_egresos'],
        'total_ganancias': totales['total_ganancias'],
    }
    return render(request, 'caja/reporte_caja.html', context)