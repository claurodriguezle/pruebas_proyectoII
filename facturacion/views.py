from django.shortcuts import redirect,render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView
from django.utils import timezone
from django.http import JsonResponse
from .models import Timbrado, Factura,DetalleFactura
from .forms import TimbradoForm, FacturaForm
from caja.models import VentaCaja
from administrador.models import Cliente, Persona, Ciudad, Barrio  # para la búsqueda
import json

# Create your views here.
# facturacion/views.py
class TimbradoListView(ListView):
    model = Timbrado
    template_name = 'timbrado/timbrado_list.html'
    context_object_name = 'timbrados'
    def get_queryset(self):
        # Solo muestra timbrados NO eliminados
        return Timbrado.objects.filter(eliminado=False)
class TimbradoCreateView(CreateView):
    model = Timbrado
    form_class = TimbradoForm
    template_name = 'timbrado/timbrado_form.html'
    success_url = reverse_lazy('facturacion:timbrado_list')

    def form_valid(self, form):
        messages.success(self.request, "✅ Timbrado creado correctamente.")
        return super().form_valid(form)

class TimbradoUpdateView(UpdateView):
    model = Timbrado
    form_class = TimbradoForm
    template_name = 'timbrado/timbrado_form.html'
    success_url = reverse_lazy('facturacion:timbrado_list')

    def form_valid(self, form):
        messages.success(self.request, "✏️ Timbrado actualizado correctamente.")
        return super().form_valid(form)

def timbrado_toggle_active(request, pk):
    timbrado = get_object_or_404(Timbrado, pk=pk)
    timbrado.activo = not timbrado.activo
    timbrado.save()
    messages.success(request, f"✅ Timbrado {'activado' if timbrado.activo else 'desactivado'} correctamente.")
    return redirect('facturacion:timbrado_list')

def timbrado_soft_delete(request, pk):
    timbrado = get_object_or_404(Timbrado, pk=pk)
    timbrado.soft_delete()  # Usamos el método que creamos
    messages.success(request, "Timbrado marcado como eliminado (no se borró de la BD).")
    return redirect('facturacion:timbrado_list')

#Vistas para Factura
def factura_view(request):
    # Buscar una factura activa, si existe
    #factura = Factura.objects.get(pk=factura_id)
    timbrado_activo = Timbrado.objects.filter(activo=True, eliminado=False).first()

    context = {
        'factura': None,
        'timbrado': timbrado_activo
    }
    return render(request, 'factura/factura.html', context)

@login_required
def factura_detalle(request, factura_id):
    factura = get_object_or_404(
        Factura.objects.select_related('cliente__persona', 'timbrado')
                       .prefetch_related('detalles__producto'),
        pk=factura_id
    )
    return render(request, 'factura/factura_detalle.html', {'factura': factura})


@login_required
def facturas_list(request):
    facturas = (
        Factura.objects
        .select_related('cliente__persona', 'timbrado')
        .order_by('-fecha_emision', '-cod_fact')
    )
    return render(request, 'factura/facturas_list.html', {'facturas': facturas})

#Vistas para emitir factura desde Caja
@login_required
def buscar_cliente_factura(request):
    """
    GET /facturacion/buscar-cliente/?q=<cedula_o_ruc>
    Devuelve JSON con los datos del cliente o un mensaje de error.
    """
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'found': False, 'error': 'Ingresá una cédula o RUC.'})
 
    persona = (
        Persona.objects.filter(cedula=q).first()
        or Persona.objects.filter(ruc=q).first()
    )
 
    if not persona:
        return JsonResponse({
            'found': False,
            'error': 'No se encontró ningún cliente con esa cédula o RUC.'
        })
 
    try:
        cliente = persona.cliente
    except Cliente.DoesNotExist:
        return JsonResponse({
            'found': False,
            'error': 'La persona existe pero no está registrada como cliente.'
        })
 
    return JsonResponse({
        'found':      True,
        'cliente_id': cliente.id,
        'nombre':     f"{persona.nombre} {persona.apellido}",
        'ruc':        persona.ruc or persona.cedula,
        'telefono':   persona.telefono,
        'ciudad':     str(persona.ciudad) if persona.ciudad_id else '',
    })
 
#Vista para emitir factura desde Caja
# ── Buscar cliente por cédula/RUC (AJAX) ─────────────────────────────────────
@login_required
def buscar_cliente_factura(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'found': False, 'error': 'Ingresá una cédula o RUC.'})
 
    persona = (
        Persona.objects.filter(cedula=q).first()
        or Persona.objects.filter(ruc=q).first()
    )
 
    if not persona:
        return JsonResponse({'found': False, 'error': 'No se encontró ningún cliente con esa cédula o RUC.'})
 
    try:
        cliente = persona.cliente
    except Cliente.DoesNotExist:
        return JsonResponse({'found': False, 'error': 'La persona existe pero no está registrada como cliente.'})
 
    return JsonResponse({
        'found':      True,
        'cliente_id': cliente.id,
        'nombre':     f"{persona.nombre} {persona.apellido}",
        'ruc':        persona.ruc or persona.cedula,
        'telefono':   persona.telefono,
        'ciudad':     str(persona.ciudad) if persona.ciudad_id else '',
    })
 
 
# ── Crear cliente rápido desde la factura (AJAX) ──────────────────────────────
@login_required
def crear_cliente_rapido(request):
    """
    POST — recibe nombre, apellido, cedula, ruc, telefono, direccion
    Crea Persona + Cliente con valores mínimos y devuelve los datos del cliente.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)
 
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Datos inválidos.'}, status=400)
 
    nombre    = data.get('nombre', '').strip()
    apellido  = data.get('apellido', '').strip()
    cedula    = data.get('cedula', '').strip()
    ruc       = data.get('ruc', '').strip() or None
    telefono  = data.get('telefono', '').strip()
    direccion = data.get('direccion', '').strip()  # solo para la factura, no se guarda en Persona
 
    # Validaciones mínimas
    if not nombre or not apellido:
        return JsonResponse({'success': False, 'error': 'Nombre y apellido son obligatorios.'})
    if not cedula:
        return JsonResponse({'success': False, 'error': 'La cédula es obligatoria.'})
    if not telefono:
        return JsonResponse({'success': False, 'error': 'El teléfono es obligatorio.'})
 
    # Verificar que la cédula no esté ya registrada
    if Persona.objects.filter(cedula=cedula).exists():
        return JsonResponse({'success': False, 'error': f'Ya existe una persona con la cédula {cedula}.'})
 
    # Verificar RUC duplicado si se ingresó
    if ruc and Persona.objects.filter(ruc=ruc).exists():
        return JsonResponse({'success': False, 'error': f'Ya existe una persona con el RUC {ruc}.'})
 
    # Valores default para campos obligatorios de Persona
    ciudad = Ciudad.objects.first()
    barrio = Barrio.objects.filter(ciudad=ciudad).first() if ciudad else Barrio.objects.first()
 
    if not ciudad or not barrio:
        return JsonResponse({
            'success': False,
            'error': 'No hay ciudades/barrios configurados en el sistema. Contactá al administrador.'
        })
 
    # Crear Persona
    persona = Persona.objects.create(
        nombre          = nombre,
        apellido        = apellido,
        cedula          = cedula,
        ruc             = ruc,
        telefono        = telefono,
        fecha_nacimiento = '2000-01-01',   # placeholder obligatorio
        nacionalidad    = 'Paraguaya',      # placeholder obligatorio
        ciudad          = ciudad,
        barrio          = barrio,
        estado          = True,
    )
 
    # Crear Cliente vinculado a la Persona
    cliente = Cliente.objects.create(persona=persona)
 
    return JsonResponse({
        'success':    True,
        'cliente_id': cliente.id,
        'nombre':     f"{persona.nombre} {persona.apellido}",
        'ruc':        persona.ruc or persona.cedula,
        'telefono':   persona.telefono,
        'direccion':  direccion,   # se devuelve para mostrarlo, no se guarda en Persona
    })
 
 
# ── Vista principal ───────────────────────────────────────────────────────────
@login_required
def emitir_factura(request, venta_id):
    venta = get_object_or_404(
        VentaCaja.objects.select_related('cliente__persona', 'cuenta__mesa', 'pedido'),
        pk=venta_id
    )
 
    if hasattr(venta, 'factura'):
        messages.info(request, "Esta venta ya tiene una factura emitida.")
        return redirect('facturacion:factura_detalle', factura_id=venta.factura.cod_fact)
 
    timbrado = Timbrado.objects.filter(activo=True, eliminado=False).first()
 
    ultima_factura   = Factura.objects.order_by('-cod_fact').first()
    siguiente_num    = (ultima_factura.cod_fact + 1) if ultima_factura else 1
    nro_fact_preview = f"001-001-{siguiente_num:07d}"
 
    # ── GET ──────────────────────────────────────────────────
    if request.method == 'GET':
        cliente_previo = None
        if venta.cliente:
            p = venta.cliente.persona
            cliente_previo = {
                'id':       venta.cliente.id,
                'nombre':   f"{p.nombre} {p.apellido}",
                'ruc':      p.ruc or p.cedula,
                'telefono': p.telefono,
                'ciudad':   str(p.ciudad) if p.ciudad_id else '',
            }
 
        return render(request, 'factura/emitir_factura.html', {
            'venta':            venta,
            'timbrado':         timbrado,
            'hoy':              timezone.now().date(),
            'nro_fact_preview': nro_fact_preview,
            'cliente_previo':   cliente_previo,
        })
 
    # ── POST ─────────────────────────────────────────────────
    if not timbrado:
        messages.error(request, "No hay timbrado activo.")
        return redirect('facturacion:timbrado_list')
 
    cliente_id = request.POST.get('cliente_id', '').strip()
    if not cliente_id:
        messages.error(request, "Debés seleccionar un cliente antes de emitir la factura.")
        return redirect(request.path)
 
    cliente = get_object_or_404(Cliente.objects.select_related('persona'), pk=cliente_id)
    persona = cliente.persona
 
    # Dirección: usar la que vino del POST (puede ser la ingresada en el form rápido)
    direccion_factura = request.POST.get('direccion_cliente', str(persona.ciudad) if persona.ciudad_id else '')
 
    ultima_factura = Factura.objects.order_by('-cod_fact').first()
    siguiente_num  = (ultima_factura.cod_fact + 1) if ultima_factura else 1
    nro_fact       = f"001-001-{siguiente_num:07d}"
 
    factura = Factura.objects.create(
        nro_fact          = nro_fact,
        timbrado          = timbrado,
        venta_caja        = venta,
        cliente           = cliente,
        nombre_cliente    = f"{persona.nombre} {persona.apellido}",
        ruc_cliente       = persona.ruc or persona.cedula,
        telefono_cliente  = persona.telefono,
        direccion_cliente = direccion_factura,
        forma_de_pago     = 'EFECTIVO',
        fecha_emision     = timezone.now().date(),
        monto_total       = venta.total,
        descuento         = 0,
    )
 
    # Detalles desde cuenta de mesa (múltiples pedidos)
    if venta.cuenta:
        for pedido in venta.cuenta.pedidos.exclude(estado_entrega='CA'):
            for item in pedido.detalle.select_related('producto').all():
                DetalleFactura.objects.create(
                    factura         = factura,
                    producto        = item.producto,
                    descripcion     = item.producto.nombre,
                    codigo_producto = item.producto.codigo,
                    cantidad        = item.cantidad,
                    precio_unitario = item.precio_unitario,
                    total           = item.precio_unitario * item.cantidad,
                )
    # Fallback: venta directa con pedido único
    elif venta.pedido:
        for item in venta.pedido.detalle.select_related('producto').all():
            DetalleFactura.objects.create(
                factura         = factura,
                producto        = item.producto,
                descripcion     = item.producto.nombre,
                codigo_producto = item.producto.codigo,
                cantidad        = item.cantidad,
                precio_unitario = item.precio_unitario,
                total           = item.precio_unitario * item.cantidad,
            )
 
    factura.calcular_totales()
    messages.success(request, f"✅ Factura {nro_fact} emitida correctamente.")
    return redirect('facturacion:factura_detalle', factura_id=factura.cod_fact)
