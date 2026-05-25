from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_GET, require_POST

from .models import Caja, Cuenta, VentaCaja, MovimientoCaja
from administrador.models import Producto, Cliente, Persona, Ciudad, Barrio, Mesa
from pedidos.models import Pedido, DetallePedido

import json
from datetime import date
from pedidos.views import descontar_stock

#Importamos los decoradores de grupos
from usuarios.decorators import grupo_requerido


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def get_caja_abierta(user):
    return Caja.objects.filter(usuario_apertura=user, estado='abierta').first()


def _get_cliente_ocasional():
    """Devuelve o crea el cliente genérico para pedidos de mesa."""
    ciudad = Ciudad.objects.first()
    barrio = Barrio.objects.first()
    if not ciudad or not barrio:
        raise ValueError(
            'No hay Ciudad ni Barrio registrados. Cargá al menos uno desde el admin.'
        )
    persona, _ = Persona.objects.get_or_create(
        cedula='0000000',
        defaults={
            'nombre': 'Cliente', 'apellido': 'Ocasional',
            'telefono': '000000000', 'fecha_nacimiento': date(2000, 1, 1),
            'nacionalidad': 'Paraguaya', 'ciudad': ciudad, 'barrio': barrio,
        }
    )
    cliente, _ = Cliente.objects.get_or_create(persona=persona)
    return cliente


# ─────────────────────────────────────────────
#  APERTURA DE CAJA
# ─────────────────────────────────────────────

@login_required
@grupo_requerido('Empleado', 'Administrador')
def apertura_caja(request):
    if get_caja_abierta(request.user):
        messages.info(request, 'Ya tenés una caja abierta.')
        return redirect('caja:punto_de_venta')

    if request.method == 'POST':
        monto_str = request.POST.get('monto_inicial', '0').replace('.', '').replace(',', '')
        try:
            monto_inicial = int(monto_str)
        except ValueError:
            monto_inicial = 0
        Caja.objects.create(
            usuario_apertura=request.user,
            monto_inicial=monto_inicial,
            monto_final_esperado=monto_inicial,
            estado='abierta',
        )
        messages.success(request, 'Caja abierta exitosamente.')
        return redirect('caja:punto_de_venta')

    return render(request, 'caja/apertura_caja.html')

# ─────────────────────────────────────────────
#  ABRIR CUENTA EN UNA MESA  (AJAX)
# ─────────────────────────────────────────────

@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_POST
def abrir_cuenta(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})

    try:
        data = json.loads(request.body)
        mesa_id = int(data['mesa_id'])
        nombre_cliente = (data.get('nombre_cliente') or '').strip()
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})

    mesa = get_object_or_404(Mesa, id=mesa_id, activa=True)

    if mesa.estado == 'ocupada':
        return JsonResponse({'success': False, 'error': f'La Mesa {mesa.numero} ya está ocupada'})

    with transaction.atomic():
        cuenta = Cuenta.objects.create(
            mesa=mesa,
            caja=caja,
            nombre_cliente=nombre_cliente or None,
        )
        mesa.estado = 'ocupada'
        mesa.save(update_fields=['estado'])

    return JsonResponse({
        'success': True,
        'cuenta_id': cuenta.id,
        'mesa_id': mesa.id,
        'mesa_numero': mesa.numero,
    })


# ─────────────────────────────────────────────
#  AGREGAR PEDIDO A UNA CUENTA  (AJAX)
# ─────────────────────────────────────────────
@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_POST
def agregar_pedido_cuenta(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})

    try:
        data = json.loads(request.body)
        cuenta_id = int(data['cuenta_id'])
        productos_data = data.get('productos', [])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})

    if not productos_data:
        return JsonResponse({'success': False, 'error': 'No hay productos en el pedido'})

    cuenta = get_object_or_404(Cuenta, id=cuenta_id, estado='abierta', caja=caja)

    # Importar modelos necesarios
    from pedidos.models import Adicional, DetalleAdicionalPedido, IngredienteEliminadoPedido, DetallePedido
    from administrador.models import IngredienteProducto
    
    total = 0
    productos_info = []
    
    for item in productos_data:
        producto_id = int(item['producto_id'])
        cantidad = int(item['cantidad'])
        adicionales_ids = [int(ad['id']) for ad in item.get('adicionales', [])]
        sin_nombres = item.get('sin', [])
        
        producto = get_object_or_404(Producto, pk=producto_id, estado='A')
        adicionales = Adicional.objects.filter(id__in=adicionales_ids, activo=True)
        
        precio_unitario = producto.precio + sum(ad.precio for ad in adicionales)
        total_item = precio_unitario * cantidad
        total += total_item
        
        productos_info.append({
            'producto': producto,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'adicionales': adicionales,
            'sin': sin_nombres,
        })
    
    try:
        cliente = _get_cliente_ocasional()
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})

    with transaction.atomic():
        pedido = Pedido.objects.create(
            cliente=cliente,
            total=total,
            tipo_entrega='RE',
            estado_cocina='PE',
            estado_entrega='PE',
            mesa=cuenta.mesa,
            cuenta=cuenta,
            origen='local',
        )
        
        for info in productos_info:
            detalle = DetallePedido.objects.create(
                pedido=pedido,
                producto=info['producto'],
                cantidad=info['cantidad'],
                precio_unitario=info['precio_unitario'],
            )
            
            # Agregar adicionales
            for adicional in info['adicionales']:
                DetalleAdicionalPedido.objects.create(
                    detalle_pedido=detalle,
                    adicional=adicional,
                    cantidad=1
                )
            
            # Agregar ingredientes eliminados
            for nombre_ing in info['sin']:
                try:
                    ingrediente_obj = IngredienteProducto.objects.get(
                        producto=info['producto'],
                        item__nombre__iexact=nombre_ing
                    )
                    IngredienteEliminadoPedido.objects.create(
                        detalle_pedido=detalle,
                        ingrediente=ingrediente_obj
                    )
                except IngredienteProducto.DoesNotExist:
                    pass
        
        # Descontar stock
        from pedidos.views import descontar_stock
        descontar_stock(pedido)

    return JsonResponse({
        'success': True,
        'pedido_id': pedido.id,
        'total_pedido': total,
        'total_cuenta': cuenta.total,
        'num_pedidos': cuenta.cantidad_pedidos,
        'nombre_cliente': cuenta.nombre_cliente or '',
    })


# ─────────────────────────────────────────────
#  VER CUENTA  (AJAX)
# ─────────────────────────────────────────────

@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_GET
def ver_cuenta(request, cuenta_id):
    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})

    cuenta = get_object_or_404(Cuenta, id=cuenta_id, caja=caja)

    pedidos_data = []
    for p in cuenta.pedidos_activos.prefetch_related('detalle__producto'):
        items = [
            {
                'nombre': d.producto.nombre,
                'cantidad': d.cantidad,
                'precio_unitario': d.precio_unitario,
                'subtotal': d.cantidad * d.precio_unitario,
            }
            for d in p.detalle.all()
        ]
        pedidos_data.append({
            'pedido_id': p.id,
            'estado_cocina': p.get_estado_cocina_display(),
            'total': p.total,
            'items': items,
        })

    return JsonResponse({
        'success': True,
        'cuenta_id': cuenta.id,
        'mesa_numero': cuenta.mesa.numero,
        'nombre_cliente': cuenta.nombre_cliente or '',
        'estado': cuenta.estado,
        'total': cuenta.total,
        'pedidos': pedidos_data,
    })


# ─────────────────────────────────────────────
#  COBRAR CUENTA  (AJAX)
# ─────────────────────────────────────────────

@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_POST
def cobrar_cuenta(request):
    caja = get_caja_abierta(request.user)
    
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})

    try:
        data = json.loads(request.body)
        cuenta_id = int(data['cuenta_id'])
        monto_recibido = int(data['monto_recibido'])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})

    cuenta = get_object_or_404(Cuenta, id=cuenta_id, estado='abierta', caja=caja)
    # ✅ Bloquear cobro si hay pedidos que no fueron entregados aún
    pedidos_pendientes = cuenta.pedidos_activos.exclude(estado_entrega__in=['EN', 'FA'])
    if pedidos_pendientes.exists():
        cantidad = pedidos_pendientes.count()
        return JsonResponse({
            'success': False,
            'error': f'Hay {cantidad} pedido(s) que aún no fueron entregados. '
                    f'Esperá que cocina los marque como listos y el mozo los entregue.'
        })
    total = cuenta.total

    if monto_recibido < total:
        return JsonResponse({
            'success': False,
            'error': f'Monto insuficiente. Total: ₲{total:,}'
        })

    vuelto = monto_recibido - total
    nombre = cuenta.nombre_cliente or f'Mesa {cuenta.mesa.numero}'

    with transaction.atomic():
        # Marcar pedidos como facturados
        cuenta.pedidos.exclude(estado_entrega='CA').update(estado_entrega='FA')

        # Cerrar cuenta
        cuenta.estado = 'cobrada'
        cuenta.fecha_cierre = timezone.now()
        cuenta.monto_cobrado = total
        cuenta.monto_recibido = monto_recibido
        cuenta.vuelto = vuelto
        cuenta.usuario_cobro = request.user
        cuenta.save(update_fields=[
            'estado', 'fecha_cierre', 'monto_cobrado',
            'monto_recibido', 'vuelto', 'usuario_cobro'
        ])

        # Liberar mesa
        mesa = cuenta.mesa
        mesa.estado = 'libre'
        mesa.save(update_fields=['estado'])

    
        # Registrar venta en caja
        venta = VentaCaja.objects.create(
            caja=caja,
            cuenta=cuenta,
            cliente_nombre=nombre,
            total=total,
            monto_recibido=monto_recibido,
            vuelto=vuelto,
            #'venta_id': venta.id,
        )

        caja.recalcular_monto_esperado()

    return JsonResponse({
        'success': True,
        'mesa_numero': mesa.numero,
        'total': total,
        'monto_recibido': monto_recibido,
        'vuelto': vuelto,
        'venta_id': venta.id,
    })


# ─────────────────────────────────────────────
#  API — estado de una mesa individual (AJAX)
# ─────────────────────────────────────────────

@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_GET
def api_mesa_estado(request, mesa_id):
    caja = get_caja_abierta(request.user)
    mesa = get_object_or_404(Mesa, id=mesa_id, activa=True)

    cuenta = None
    if caja:
        cuenta = mesa.cuentas.filter(estado='abierta', caja=caja).first()

    return JsonResponse({
        'success': True,
        'mesa_id': mesa.id,
        'numero': mesa.numero,
        'estado': mesa.estado,
        'cuenta_id': cuenta.id if cuenta else None,
    })


# ─────────────────────────────────────────────
#  API — estado de TODAS las mesas (AJAX)
# ─────────────────────────────────────────────

@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_GET
def api_todas_mesas_estado(request):
    """Usado por el botón Sincronizar del POS."""
    caja = get_caja_abierta(request.user)
    mesas_qs = Mesa.objects.filter(activa=True)

    result = []
    for mesa in mesas_qs:
        cuenta = None
        if caja:
            cuenta = mesa.cuentas.filter(estado='abierta', caja=caja).first()
        result.append({
            'id': mesa.id,
            'numero': mesa.numero,
            'estado': mesa.estado,
            'cuenta_id': cuenta.id if cuenta else None,
            'total': cuenta.total if cuenta else 0,
            'num_pedidos': cuenta.cantidad_pedidos if cuenta else 0,
            'nombre_cliente': cuenta.nombre_cliente or '' if cuenta else '',
        })

    return JsonResponse({'success': True, 'mesas': result})


# ─────────────────────────────────────────────
@login_required
@grupo_requerido('Empleado', 'Administrador')
def cierre_caja(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.error(request, 'No hay caja abierta para cerrar.')
        return redirect('caja:apertura_caja')

    mesas_abiertas = caja.cuentas.filter(estado='abierta').count()
    caja.recalcular_monto_esperado()
    totales = {
        'ventas': caja.total_ventas,
        'egresos': caja.total_egresos,
        'ganancia': caja.total_ventas - caja.total_egresos,
    }
    
    # 🔥 NUEVO: Calcular resumen de ventas por origen (Local vs Online)
    from django.db.models import Sum, Count, Q, Value, CharField
    from django.db.models.functions import Coalesce
    
    # Obtener todas las ventas de esta caja
    ventas_caja = caja.ventas.filter(anulado=False)
    
    # Ventas locales (pedidos de mesa/mostrador)
    # Incluye: ventas con pedido origen='local' O ventas sin pedido (mostrador directo)
    ventas_locales = ventas_caja.filter(
        Q(pedido__origen='local') | Q(pedido__isnull=True)
    ).aggregate(
        total=Coalesce(Sum('total'), 0),
        cantidad=Coalesce(Count('id'), 0)
    )
    
    # Ventas online
    ventas_online = ventas_caja.filter(
        pedido__origen='online'
    ).aggregate(
        total=Coalesce(Sum('total'), 0),
        cantidad=Coalesce(Count('id'), 0)
    )
    
    # Calcular porcentajes
    total_ventas = totales['ventas']
    
    if total_ventas > 0:
        porcentaje_local = (ventas_locales['total'] or 0) * 100 / total_ventas
        porcentaje_online = (ventas_online['total'] or 0) * 100 / total_ventas
    else:
        porcentaje_local = 0
        porcentaje_online = 0
    
    resumen_ventas = {
        'local': {
            'total': ventas_locales['total'] or 0,
            'cantidad': ventas_locales['cantidad'] or 0,
            'porcentaje': round(porcentaje_local, 1)
        },
        'online': {
            'total': ventas_online['total'] or 0,
            'cantidad': ventas_online['cantidad'] or 0,
            'porcentaje': round(porcentaje_online, 1)
        }
    }
    
    # Obtener ventas recientes CON origen incluido
    ventas_recientes = caja.ventas.filter(anulado=False).select_related(
        'pedido__cliente__persona', 'cliente__persona'
    ).order_by('-fecha')[:15]
    
    # Enriquecer cada venta con su origen
    for venta in ventas_recientes:
        if venta.pedido:
            venta.origen = venta.pedido.origen
        else:
            venta.origen = 'local'  # Ventas directas de mostrador

    if request.method == 'POST':
        monto_str = request.POST.get('monto_final_real', '0').replace('.', '').replace(',', '')
        try:
            monto_final_real = int(monto_str)
        except ValueError:
            monto_final_real = 0

        with transaction.atomic():
            Caja.objects.filter(pk=caja.pk).update(
                monto_final_real=monto_final_real,
                observaciones_cierre=request.POST.get('observaciones', ''),
                fecha_cierre=timezone.now(),
                usuario_cierre=request.user,
                estado='cerrada',
            )

        # Recargar desde BD para tener el objeto actualizado
        caja.refresh_from_db()

        return render(request, 'caja/resumen_cierre.html', {
            'caja': caja,
            'totales': totales,
            'resumen_ventas': resumen_ventas,  # ← pasar también al resumen
            'diferencia': caja.diferencia,
        })

    return render(request, 'caja/cierre_caja.html', {
        'caja': caja,
        'totales': totales,
        'resumen_ventas': resumen_ventas,  # ← nuevo
        'movimientos': caja.movimientos.order_by('-fecha'),
        'ventas_recientes': ventas_recientes,  # ← ahora incluye origen
        'mesas_abiertas': mesas_abiertas,
    })

#Ventas recientes en el POS

@login_required
@grupo_requerido('Empleado', 'Administrador')
def punto_de_venta(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.warning(request, 'Debés abrir la caja antes de operar.')
        return redirect('caja:apertura_caja')

    mesas_qs = Mesa.objects.filter(activa=True).prefetch_related(
        'cuentas__pedidos__detalle__producto'
    )

    mesas = []
    for mesa in mesas_qs:
        cuenta = mesa.cuentas.filter(estado='abierta', caja=caja).first()
        num_pedidos = cuenta.cantidad_pedidos if cuenta else 0
        total = cuenta.total if cuenta else 0
        mesas.append({
            'mesa': mesa,
            'cuenta': cuenta,
            'num_pedidos': num_pedidos,
            'total': total,
        })

    productos = (
        Producto.objects
        .filter(estado='A')
        .select_related('categoria')
        .order_by('categoria', 'nombre')
    )

    # ── NUEVO: últimas ventas de la caja actual ──
    ventas_recientes = (
        caja.ventas
        .filter(anulado=False)
        .select_related('pedido', 'cuenta__mesa')
        .order_by('-fecha')[:15]
    )

    return render(request, 'caja/punto_de_venta.html', {
        'caja': caja,
        'mesas': mesas,
        'productos': productos,
        'ventas_recientes': ventas_recientes,  # ← nuevo
    })


# FACTURAR PEDIDOS PENDIENTES DESDE CAJA

@login_required
@grupo_requerido('Empleado', 'Administrador')
def pedidos_para_facturar(request):
    """Lista los pedidos que están en estado 'PP' (Pendiente Pago) para facturar desde caja"""
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.error(request, 'Debés abrir la caja primero.')
        return redirect('caja:apertura_caja')
    
    # Obtener pedidos con estado 'PP' (Pendiente Pago)
    pedidos_pendientes = Pedido.objects.filter(
        estado_entrega='PP'
    ).select_related(
        'cliente__persona'
    ).prefetch_related(
        'detalle__producto',
        'detalle__adicionales__adicional'
    ).order_by('-fecha')
    
    return render(request, 'caja/pedidos_para_facturar.html', {
        'caja': caja,
        'pedidos': pedidos_pendientes,
    })


@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_POST
def facturar_desde_caja(request, pedido_id):
    from facturacion.services import generar_factura_desde_pedido
    
    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})
    
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    # Permitir facturar solo si está en PP o EN
    if pedido.estado_entrega not in ['PP', 'EN']:
        return JsonResponse({'success': False, 'error': f'El pedido está en estado {pedido.get_estado_entrega_display()}, no se puede facturar'})
    try:
        with transaction.atomic():
            factura = generar_factura_desde_pedido(pedido)

            if factura:
                pedido.estado_entrega = 'FA'
                pedido.save(update_fields=['estado_entrega'])

                # Registrar venta en caja si no existe
                if not hasattr(pedido, 'venta_caja'):
                    total_con_delivery = pedido.total + (pedido.costo_delivery or 0)
                    VentaCaja.objects.create(
                        caja=caja,
                        pedido=pedido,
                        cliente=pedido.cliente,
                        total=total_con_delivery,
                        monto_recibido=total_con_delivery,
                        vuelto=0,
                        tipo_entrega=pedido.tipo_entrega,
                    )
                    caja.recalcular_monto_esperado()

                return JsonResponse({
                    'success': True,
                    'message': 'Factura generada correctamente',
                    'nro_factura': factura.nro_fact,
                    'factura_id': factura.cod_fact
                })
            else:
                return JsonResponse({'success': False, 'error': 'No se pudo generar la factura. Verifique timbrado activo.'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@grupo_requerido('Empleado', 'Administrador')
@require_GET
def api_pedidos_pendientes(request):
    """Retorna los pedidos en estado PP (Pendiente Pago) para facturar desde caja"""
    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'error': 'No hay caja abierta'}, status=400)
    
    pedidos = Pedido.objects.filter(
        estado_entrega='PP'
    ).select_related('cliente__persona').order_by('fecha')
    
    data = {
        'pedidos': [
            {
                'id': p.id,
                'cliente_nombre': f"{p.cliente.persona.nombre} {p.cliente.persona.apellido}",
                'total': f"{p.total:,}".replace(',', '.'),
                'fecha': p.fecha.strftime('%d/%m %H:%M'),
                'tipo_entrega_display': p.get_tipo_entrega_display(),
            }
            for p in pedidos
        ]
    }
    return JsonResponse(data)

@login_required
@grupo_requerido('Empleado', 'Administrador')
@require_POST
def pos_cancelar_pedido(request, pedido_id):
    """Cancela un pedido local del POS y devuelve el stock al inventario."""
    from pedidos.views import devolver_stock

    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta.'})

    pedido = get_object_or_404(Pedido, pk=pedido_id)

    # Solo se puede cancelar si cocina aún no empezó a prepararlo
    if pedido.estado_cocina != 'PE':
        return JsonResponse({
            'success': False,
            'error': 'No se puede cancelar: el pedido ya está en preparación.'
        })

    if pedido.estado_entrega == 'CA':
        return JsonResponse({'success': False, 'error': 'El pedido ya estaba cancelado.'})

    with transaction.atomic():
        devolver_stock(pedido)
        pedido.estado_entrega = 'CA'
        pedido.save(update_fields=['estado_entrega'])

    return JsonResponse({
        'success': True,
        'pedido_id': pedido.id,
        'mensaje': f'Pedido #{pedido.id} cancelado y stock restaurado.'
    })