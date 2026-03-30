from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib import messages

from .models import Caja, VentaCaja, MovimientoCaja
from administrador.models import Producto, Cliente, Persona, Ciudad, Barrio
from pedidos.models import Pedido, DetallePedido

import json
from datetime import date


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def get_caja_abierta(user):
    """Devuelve la caja abierta del usuario, o None."""
    return Caja.objects.filter(usuario_apertura=user, estado='abierta').first()


def _get_or_create_cliente_ocasional():
    """
    Devuelve el cliente "Ocasional" usado cuando no se especifica cliente.
    Requiere que exista al menos una Ciudad y un Barrio en la BD.
    """
    ciudad = Ciudad.objects.first()
    barrio = Barrio.objects.first()
    if not ciudad or not barrio:
        raise ValueError(
            "No hay Ciudad ni Barrio registrados. "
            "Cargá al menos uno desde el admin para poder operar."
        )
    persona, _ = Persona.objects.get_or_create(
        cedula='0000000',
        defaults={
            'nombre': 'Cliente',
            'apellido': 'Ocasional',
            'telefono': '000000000',
            'fecha_nacimiento': date(2000, 1, 1),
            'nacionalidad': 'Paraguaya',
            'ciudad': ciudad,
            'barrio': barrio,
        }
    )
    cliente, _ = Cliente.objects.get_or_create(persona=persona)
    return cliente


def _crear_cliente_desde_nombre(nombre_completo, ciudad, barrio):
    """
    Crea una Persona + Cliente con el nombre ingresado desde la caja.
    Si ya existe alguien con ese nombre, lo reutiliza.
    """
    partes = nombre_completo.strip().split(' ', 1)
    nombre = partes[0]
    apellido = partes[1] if len(partes) > 1 else 'S/A'

    # Cedula temporal única basada en timestamp para no colisionar
    import time
    cedula_temp = f'CAJA-{int(time.time())}'

    persona = Persona.objects.create(
        nombre=nombre,
        apellido=apellido,
        cedula=cedula_temp,
        telefono='000000000',
        fecha_nacimiento=date(2000, 1, 1),
        nacionalidad='Paraguaya',
        ciudad=ciudad,
        barrio=barrio,
    )
    cliente = Cliente.objects.create(persona=persona)
    return cliente


# ─────────────────────────────────────────────
#  APERTURA DE CAJA
# ─────────────────────────────────────────────

@login_required
def apertura_caja(request):
    caja_existente = get_caja_abierta(request.user)
    if caja_existente:
        messages.info(request, "Ya tenés una caja abierta.")
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
        messages.success(request, "Caja abierta exitosamente.")
        return redirect('caja:punto_de_venta')

    return render(request, 'caja/apertura_caja.html')


# ─────────────────────────────────────────────
#  PUNTO DE VENTA (POS)
# ─────────────────────────────────────────────

@login_required
def punto_de_venta(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.warning(request, "Debes abrir la caja antes de operar.")
        return redirect('caja:apertura_caja')

    productos = Producto.objects.filter(estado='A').select_related('categoria').order_by('categoria', 'nombre')
    clientes = Cliente.objects.select_related('persona').exclude(
        persona__cedula='0000000'   # excluir el cliente ocasional del selector
    ).order_by('persona__nombre')

    context = {
        'caja': caja,
        'productos': productos,
        'clientes': clientes,
    }
    return render(request, 'caja/punto_de_venta.html', context)


# ─────────────────────────────────────────────
#  COMPLETAR VENTA (AJAX)
# ─────────────────────────────────────────────

@login_required
def completar_venta(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    caja = get_caja_abierta(request.user)
    if not caja:
        return JsonResponse({'success': False, 'error': 'No hay caja abierta'})

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'})

    productos_data = data.get('productos', [])
    monto_recibido = int(data.get('monto_recibido', 0))
    cliente_id = data.get('cliente_id') or None
    cliente_nombre = (data.get('cliente_nombre') or '').strip() or None
    tipo_entrega = data.get('tipo_entrega', 'RE')

    if not productos_data:
        return JsonResponse({'success': False, 'error': 'No hay productos en la venta'})

    # Verificar productos y calcular total
    ids = [int(p['producto_id']) for p in productos_data]
    productos_db = {p.id: p for p in Producto.objects.filter(id__in=ids, estado='A')}

    total = 0
    for item in productos_data:
        pid = int(item['producto_id'])
        if pid not in productos_db:
            return JsonResponse({'success': False, 'error': f'Producto #{pid} no encontrado o inactivo'})
        total += productos_db[pid].precio * int(item['cantidad'])

    if monto_recibido < total:
        return JsonResponse({
            'success': False,
            'error': f'Monto insuficiente. Total: ₲{total:,}'
        })

    vuelto = monto_recibido - total

    # ── Resolver cliente ──────────────────────────────
    try:
        ciudad = Ciudad.objects.first()
        barrio = Barrio.objects.first()

        if cliente_id:
            # Cliente registrado seleccionado
            try:
                cliente = Cliente.objects.get(id=int(cliente_id))
            except Cliente.DoesNotExist:
                cliente = _get_or_create_cliente_ocasional()

        elif cliente_nombre:
            # Nombre ingresado manualmente desde caja
            cliente = _crear_cliente_desde_nombre(cliente_nombre, ciudad, barrio)

        else:
            # Sin datos → cliente ocasional
            cliente = _get_or_create_cliente_ocasional()

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})

    # ── Crear pedido + venta en una transacción ───────
    with transaction.atomic():
        # Pedido — estado 'PE' (Pendiente) en cocina para que aparezca en el panel
        pedido = Pedido.objects.create(
            cliente=cliente,
            total=total,
            tipo_entrega=tipo_entrega,
            estado_cocina='PE',    # pendiente → aparece en panel de cocina
            estado_entrega='PE',   # pendiente → aparece en panel de empleado
        )

        # Detalles del pedido
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

        # Registrar en caja
        venta = VentaCaja.objects.create(
            caja=caja,
            pedido=pedido,
            cliente=cliente,
            total=total,
            monto_recibido=monto_recibido,
            vuelto=vuelto,
            tipo_entrega=tipo_entrega,
        )

        # Actualizar monto esperado
        caja.recalcular_monto_esperado()

    return JsonResponse({
        'success': True,
        'pedido_id': pedido.id,
        'venta_id': venta.id,
        'total': total,
        'monto_recibido': monto_recibido,
        'vuelto': vuelto,
    })


# ─────────────────────────────────────────────
#  REGISTRAR EGRESO (AJAX)
# ─────────────────────────────────────────────

@login_required
def registrar_egreso(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

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
        caja=caja,
        tipo='egreso',
        descripcion=descripcion,
        monto=monto,
        usuario=request.user,
    )
    caja.recalcular_monto_esperado()

    return JsonResponse({
        'success': True,
        'mensaje': f'Egreso de ₲{monto:,} registrado correctamente.',
        'nuevo_esperado': caja.monto_final_esperado,
    })


# ─────────────────────────────────────────────
#  CIERRE DE CAJA
# ─────────────────────────────────────────────

@login_required
def cierre_caja(request):
    caja = get_caja_abierta(request.user)
    if not caja:
        messages.error(request, "No hay caja abierta para cerrar.")
        return redirect('caja:reporte_caja')

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

    ventas_recientes = caja.ventas.filter(anulado=False).select_related(
        'cliente__persona'
    ).order_by('-fecha')[:10]

    context = {
        'caja': caja,
        'totales': totales,
        'movimientos': caja.movimientos.order_by('-fecha'),
        'ventas_recientes': ventas_recientes,
    }
    return render(request, 'caja/cierre_caja.html', context)


# ─────────────────────────────────────────────
#  REPORTE DE CAJAS
# ─────────────────────────────────────────────

@login_required
def reporte_caja(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    cajas = Caja.objects.prefetch_related('ventas', 'movimientos')
    if fecha_inicio:
        cajas = cajas.filter(fecha_apertura__date__gte=fecha_inicio)
    if fecha_fin:
        cajas = cajas.filter(fecha_apertura__date__lte=fecha_fin)

    cajas_data = []
    for c in cajas:
        ventas = c.total_ventas
        egresos = c.total_egresos
        cajas_data.append({
            'obj': c,
            'ventas': ventas,
            'egresos': egresos,
            'ganancia': ventas - egresos,
        })

    context = {
        'cajas': cajas_data,
        'total_ventas': sum(c['ventas'] for c in cajas_data),
        'total_egresos': sum(c['egresos'] for c in cajas_data),
        'total_ganancias': sum(c['ganancia'] for c in cajas_data),
    }
    return render(request, 'caja/reporte_caja.html', context)