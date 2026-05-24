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
    fecha_str = request.GET.get('fecha')
    
    if fecha_str:
        fecha = datetime.date.fromisoformat(fecha_str)
    else:
        fecha = timezone.now().date()

    categoria = request.GET.get('categoria', '')
    
    egresos = Egreso.objects.filter(
        estado='ACTIVO'
    ).select_related('proveedor', 'caja', 'usuario')

    egresos = egresos.filter(fecha=fecha)

    if categoria:
        egresos = egresos.filter(categoria=categoria)

    compras = Compra.objects.filter(
        fecha=fecha,
        estado='ACTIVA'
    ).select_related('proveedor')

    total_egresos = sum(e.monto for e in egresos)
    total_compras = sum(c.monto_total for c in compras)
    total_general = total_egresos + total_compras

    context = {
        'egresos': egresos,
        'compras': compras,
        'total_egresos': total_egresos,
        'total_compras': total_compras,
        'total_general': total_general,
        'fecha_filtro': fecha,
        'categoria_filtro': categoria,
        'categorias': Egreso.CATEGORIA_CHOICES,
    }

    print(f"Fecha filtro: {fecha} tipo: {type(fecha)}")
    print(f"Compras encontradas: {compras.count()}")
    print(f"Todas las compras de hoy: {Compra.objects.filter(fecha=fecha).count()}")
    return render(request, 'egresos/lista_egresos.html', context)


@login_required
def crear_egreso(request):
    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            egreso = form.save(commit=False)
            egreso.usuario = request.user

            # Si salió de la caja, buscar la caja abierta
            if egreso.salio_de_caja:
                caja_abierta = Caja.objects.filter(estado='abierta').first()
                if caja_abierta:
                    egreso.caja = caja_abierta
                else:
                    form.add_error('salio_de_caja', 'No hay una caja abierta en este momento.')
                    return render(request, 'egresos/form_egreso.html', {'form': form, 'titulo': 'Nuevo Egreso'})

            egreso.save()
            if egreso.caja:
                egreso.caja.recalcular_monto_esperado()

            if request.headers.get('HX-Request'):
                return render(request, 'egresos/partials/tabla_egresos.html', {
                    'egresos': Egreso.objects.filter(estado='ACTIVO').select_related('proveedor', 'caja')
                })
            return redirect('egresos:lista_egresos')
    else:
        form = EgresoForm()

    return render(request, 'egresos/form_egreso.html', {
        'form': form,
        'titulo': 'Nuevo Egreso'
    })


@login_required
def editar_egreso(request, pk):
    egreso = get_object_or_404(Egreso, pk=pk, estado='ACTIVO')

    if request.method == 'POST':
        form = EgresoForm(request.POST, instance=egreso)
        if form.is_valid():
            egreso = form.save(commit=False)

            # Recalcular caja si cambió salio_de_caja
            if egreso.salio_de_caja:
                caja_abierta = Caja.objects.filter(estado='abierta').first()
                if caja_abierta:
                    egreso.caja = caja_abierta
                else:
                    form.add_error('salio_de_caja', 'No hay una caja abierta en este momento.')
                    return render(request, 'egresos/form_egreso.html', {'form': form, 'titulo': 'Editar Egreso'})
            else:
                egreso.caja = None

            egreso.save()
            if egreso.caja:
                egreso.caja.recalcular_monto_esperado()

            if request.headers.get('HX-Request'):
                return render(request, 'egresos/partials/tabla_egresos.html', {
                    'egresos': Egreso.objects.filter(estado='ACTIVO').select_related('proveedor', 'caja')
                })
            return redirect('egresos:lista_egresos')
    else:
        form = EgresoForm(instance=egreso)

    return render(request, 'egresos/form_egreso.html', {
        'form': form,
        'titulo': 'Editar Egreso',
        'egreso': egreso,
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

    if hasattr(compra, 'egreso'):
        return redirect('egresos:lista_egresos')

    if request.method == 'POST':
        form = EgresoCompraForm(request.POST)
        if form.is_valid():
            salio_de_caja = form.cleaned_data['salio_de_caja']
            caja = None

            if salio_de_caja:
                caja = Caja.objects.filter(estado='abierta').first()
                if not caja:
                    form.add_error('salio_de_caja', 'No hay una caja abierta en este momento.')
                    return render(request, 'egresos/form_compra_egreso.html', {
                        'form': form,
                        'compra': compra
                    })

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
    })