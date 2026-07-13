from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import datetime
from django.db.models import Q
from .models import Egreso
from .forms import EgresoForm, AnulacionForm, EgresoCompraForm
from administrador.models import Compra
from caja.models import Caja

@login_required
def lista_egresos(request):
    fecha_desde_str = request.GET.get('fecha_desde')
    fecha_hasta_str = request.GET.get('fecha_hasta')
    categoria = request.GET.get('categoria', '')
    hay_filtros = fecha_desde_str or fecha_hasta_str or categoria

    egresos = Egreso.objects.filter(
        estado='ACTIVO'
    ).select_related('proveedor', 'caja', 'usuario')

    if not hay_filtros:
        # Por defecto: egresos de hoy
        egresos = egresos.filter(fecha=timezone.now().date())
    else:
        # Si hay rango de fechas
        if fecha_desde_str:
            fecha_desde = datetime.date.fromisoformat(fecha_desde_str)
            egresos = egresos.filter(fecha__gte=fecha_desde)
        if fecha_hasta_str:
            fecha_hasta = datetime.date.fromisoformat(fecha_hasta_str)
            egresos = egresos.filter(fecha__lte=fecha_hasta)
        # Si solo hay categoría sin fechas → trae todos de esa categoría
        if categoria:
            egresos = egresos.filter(categoria=categoria)

    compras_pendientes = Compra.objects.filter(
        estado='ACTIVA',
        egreso__isnull=True
    ).select_related('proveedor')

    total_egresos = sum(e.monto for e in egresos)

    context = {
        'egresos': egresos,
        'compras_pendientes': compras_pendientes,
        'total_egresos': total_egresos,
        'fecha_desde_filtro': fecha_desde_str or '',
        'fecha_hasta_filtro': fecha_hasta_str or '',
        'categoria_filtro': categoria,
        'categorias': Egreso.CATEGORIA_CHOICES,
        'hay_filtros': hay_filtros,
    }
    return render(request, 'egresos/lista_egresos.html', context)


@login_required
def crear_egreso(request):
    caja_abierta = Caja.objects.filter(estado='abierta').first()

    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            salio_de_caja = form.cleaned_data['salio_de_caja']
            caja = None

            if salio_de_caja:
                if not caja_abierta:
                    form.add_error('salio_de_caja', 'No hay una caja abierta en este momento.')
                    return render(request, 'egresos/form_egreso.html', {
                        'form': form,
                        'titulo': 'Nuevo Egreso',
                        'caja_abierta': caja_abierta,
                    })
                caja = caja_abierta

            egreso = form.save(commit=False)
            egreso.usuario = request.user
            egreso.caja = caja
            egreso.save()
            if egreso.caja:
                egreso.caja.recalcular_monto_esperado()

            return redirect('egresos:lista_egresos')
    else:
        form = EgresoForm()

    return render(request, 'egresos/form_egreso.html', {
        'form': form,
        'titulo': 'Nuevo Egreso',
        'caja_abierta': caja_abierta,
    })

@login_required
def anular_egreso(request, pk):
    egreso = get_object_or_404(Egreso, pk=pk, estado='ACTIVO')

    if request.method == 'POST':
        form = AnulacionForm(request.POST)
        if form.is_valid():
            egreso.estado = 'ANULADO'
            egreso.motivo_anulacion = form.cleaned_data['motivo_anulacion']
            egreso.save()
            if egreso.caja:
                egreso.caja.recalcular_monto_esperado()

            if request.headers.get('HX-Request'):
                return render(request, 'egresos/partials/tabla_egresos.html', {
                    'egresos': Egreso.objects.filter(estado='ACTIVO').select_related('proveedor', 'caja')
                })
            return redirect('egresos:lista_egresos')
    else:
        form = AnulacionForm()

    return render(request, 'egresos/partials/modal_anulacion.html', {
        'form': form,
        'egreso': egreso,
    })

@login_required
def registrar_compra_como_egreso(request, compra_pk):
    compra = get_object_or_404(Compra, pk=compra_pk, estado='ACTIVA')
    caja_abierta = Caja.objects.filter(estado='abierta').first()

    if hasattr(compra, 'egreso'):
        return redirect('egresos:lista_egresos')

    if request.method == 'POST':
        form = EgresoCompraForm(request.POST)
        if form.is_valid():
            salio_de_caja = form.cleaned_data['salio_de_caja']
            caja = None

            if salio_de_caja:
                if not caja_abierta:  # caja_abierta, no caja
                    form.add_error('salio_de_caja', 'No hay una caja abierta en este momento.')
                    return render(request, 'egresos/form_compra_egreso.html', {
                        'form': form,
                        'compra': compra
                    })
                caja = caja_abierta  # asigna solo si existe

            egreso = Egreso.objects.create(
                fecha=compra.fecha,
                monto=compra.monto_total,
                descripcion=f"Compra #{compra.numero_factura}",
                categoria='COMPRAS',
                proveedor=compra.proveedor,
                numero_comprobante=compra.numero_factura,
                compra=compra,
                salio_de_caja=salio_de_caja,
                caja=caja,
                usuario=request.user
            )
            if egreso.caja:
                egreso.caja.recalcular_monto_esperado()

            return redirect('egresos:lista_egresos')
    else:
        form = EgresoCompraForm()

    return render(request, 'egresos/form_compra_egreso.html', {
        'form': form,
        'compra': compra,
        'caja': caja_abierta,
    })

@login_required
def lista_anulados(request):
    egresos_anulados = Egreso.objects.filter(
        estado='ANULADO'
    ).select_related('proveedor', 'caja').order_by('-fecha_registro')

    context = {
        'egresos_anulados': egresos_anulados,
    }
    return render(request, 'egresos/lista_anulados.html', context)

@login_required
def detalle_anulado(request, pk):
    egreso = get_object_or_404(Egreso, pk=pk, estado='ANULADO')
    return render(request, 'egresos/partials/modal_detalle_anulado.html', {
        'egreso': egreso,
    })