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
#  PUNTO DE VENTA — vista principal con mesas
# ─────────────────────────────────────────────

@login_required
def punto_de_venta(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.warning(request, 'Debés abrir la caja antes de operar.')
        return redirect('caja:apertura_caja')

    mesas_qs = Mesa.objects.filter(activa=True).prefetch_related(
        'cuentas__pedidos__detalle__producto'
    )

    # Armar lista de items para el template
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

    return render(request, 'caja/punto_de_venta.html', {
        'caja': caja,
        'mesas': mesas,
        'productos': productos,
    })


# ─────────────────────────────────────────────
#  ABRIR CUENTA EN UNA MESA  (AJAX)
# ─────────────────────────────────────────────

@login_required
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

    ids = [int(p['producto_id']) for p in productos_data]
    productos_db = {p.id: p for p in Producto.objects.filter(id__in=ids, estado='A')}

    total = 0
    for item in productos_data:
        pid = int(item['producto_id'])
        if pid not in productos_db:
            return JsonResponse({'success': False, 'error': f'Producto #{pid} no encontrado'})
        total += productos_db[pid].precio * int(item['cantidad'])

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
        )
        for item in productos_data:
            pid = int(item['producto_id'])
            cantidad = int(item['cantidad'])
            prod = productos_db[pid]
            DetallePedido.objects.create(
                pedido=pedido,
                producto=prod,
                cantidad=cantidad,
                precio_unitario=prod.precio,
            )
        descontar_stock(pedido)

    return JsonResponse({
        'success': True,
        'pedido_id': pedido.id,
        'total_pedido': total,
        'total_cuenta': cuenta.total,
    })


# ─────────────────────────────────────────────
#  VER CUENTA  (AJAX)
# ─────────────────────────────────────────────

@login_required
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
#  REGISTRAR EGRESO  (AJAX)
# ─────────────────────────────────────────────

@login_required
@require_POST
def registrar_egreso(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})

    try:
        data = json.loads(request.body)
        descripcion = data.get('descripcion', '').strip()
        monto = int(data.get('monto', 0))
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Datos inválidos'})

    if not descripcion:
        return JsonResponse({'success': False, 'error': 'La descripción es obligatoria'})
    if monto <= 0:
        return JsonResponse({'success': False, 'error': 'El monto debe ser mayor a 0'})

    MovimientoCaja.objects.create(
        caja=caja, tipo='egreso', descripcion=descripcion,
        monto=monto, usuario=request.user,
    )
    caja.recalcular_monto_esperado()

    return JsonResponse({'success': True, 'mensaje': f'Egreso de ₲{monto:,} registrado.'})


# ─────────────────────────────────────────────
#  CIERRE DE CAJA
# ─────────────────────────────────────────────

@login_required
def cierre_caja(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.error(request, 'No hay caja abierta para cerrar.')
        return redirect('caja:reporte_caja')

    mesas_abiertas = caja.cuentas.filter(estado='abierta').count()
    caja.recalcular_monto_esperado()
    totales = {
        'ventas': caja.total_ventas,
        'egresos': caja.total_egresos,
        'ganancia': caja.total_ventas - caja.total_egresos,
    }

    if request.method == 'POST':
        monto_str = request.POST.get('monto_final_real', '0').replace('.', '').replace(',', '')
        try:
            monto_final_real = int(monto_str)
        except ValueError:
            monto_final_real = 0

        with transaction.atomic():
            caja.monto_final_real = monto_final_real
            caja.observaciones_cierre = request.POST.get('observaciones', '')
            caja.fecha_cierre = timezone.now()
            caja.usuario_cierre = request.user
            caja.estado = 'cerrada'
            caja.save()

        return render(request, 'caja/resumen_cierre.html', {
            'caja': caja,
            'totales': totales,
            'diferencia': caja.diferencia,
        })

    return render(request, 'caja/cierre_caja.html', {
        'caja': caja,
        'totales': totales,
        'movimientos': caja.movimientos.order_by('-fecha'),
        'ventas_recientes': caja.ventas.filter(anulado=False).order_by('-fecha')[:10],
        'mesas_abiertas': mesas_abiertas,
    })


# ─────────────────────────────────────────────
#  REPORTE DE CAJAS
# ─────────────────────────────────────────────

@login_required
def reporte_caja(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin    = request.GET.get('fecha_fin')

    cajas = Caja.objects.prefetch_related('ventas', 'movimientos')
    if fecha_inicio:
        cajas = cajas.filter(fecha_apertura__date__gte=fecha_inicio)
    if fecha_fin:
        cajas = cajas.filter(fecha_apertura__date__lte=fecha_fin)

    cajas_data = []
    for c in cajas:
        v = c.total_ventas
        e = c.total_egresos
        cajas_data.append({'obj': c, 'ventas': v, 'egresos': e, 'ganancia': v - e})

    return render(request, 'caja/reporte_caja.html', {
        'cajas': cajas_data,
        'total_ventas':    sum(c['ventas']   for c in cajas_data),
        'total_egresos':   sum(c['egresos']  for c in cajas_data),
        'total_ganancias': sum(c['ganancia'] for c in cajas_data),
    })