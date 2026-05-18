"""
facturacion/services.py
───────────────────────
Lógica de negocio para generar facturas desde pedidos.
"""

from django.utils import timezone
from decimal import Decimal
from .models import Factura, DetalleFactura, Timbrado


def generar_numero_factura(timbrado):
    """
    Genera el próximo número de factura en formato 001-001-XXXXXXX.
    """
    ultima = (
        Factura.objects
        .filter(timbrado=timbrado)
        .order_by('-cod_fact')
        .first()
    )

    if ultima:
        try:
            secuencial = int(ultima.nro_fact.split('-')[-1]) + 1
        except (ValueError, IndexError):
            secuencial = 1
    else:
        secuencial = 1

    return f"001-001-{str(secuencial).zfill(7)}"


def obtener_o_crear_producto_delivery(costo_delivery):
    """
    Obtiene o crea el producto de delivery.
    """
    from administrador.models import Producto, CategoriaProducto
    
    # Buscar producto existente
    producto = Producto.objects.filter(codigo='DELIVERY-001').first()
    
    if producto:
        # Actualizar precio por si cambió
        if producto.precio != costo_delivery:
            producto.precio = costo_delivery
            producto.save(update_fields=['precio'])
        return producto
    
    # Obtener o crear categoría Servicios
    categoria_servicios, _ = CategoriaProducto.objects.get_or_create(
        nombre_categ='Servicios',
        defaults={'descripcion': 'Servicios adicionales (delivery, etc.)'}
    )
    
    # Crear producto - SIN campo 'tipo' porque no existe
    producto = Producto.objects.create(
        codigo='DELIVERY-001',
        nombre='Costo de Delivery',
        precio=costo_delivery,
        categoria=categoria_servicios,
        estado='I',
        personalizable=False,  # El delivery no se puede personalizar
    )
    return producto


def generar_factura_desde_pedido(pedido):
    """
    Genera una Factura y sus DetalleFactura a partir de un Pedido.
    Incluye el costo de delivery como un item separado.
    """
    # ── Verificar timbrado activo ────────────────────────────────────────────
    timbrado = Timbrado.objects.filter(activo=True, eliminado=False).first()
    if not timbrado:
        return None

    # ── Datos del cliente ────────────────────────────────────────────────────
    persona = pedido.cliente.persona
    ruc_o_ci = persona.ruc if persona.ruc else persona.cedula
    direccion = (
        f"{persona.barrio.nombre}, {persona.ciudad.nombre}"
        if persona.barrio and persona.ciudad
        else pedido.direccion_snapshot or ""
    )

    # ── Crear la factura ─────────────────────────────────────────────────────
    nro_fact = generar_numero_factura(timbrado)

    factura = Factura.objects.create(
        nro_fact         = nro_fact,
        pedido           = pedido,
        cliente          = pedido.cliente,
        timbrado         = timbrado,
        nombre_cliente   = f"{persona.nombre} {persona.apellido}",
        direccion_cliente= direccion,
        telefono_cliente = persona.telefono or "",
        ruc_cliente      = ruc_o_ci,
        monto_total      = pedido.total,
        forma_de_pago    = "EFECTIVO",
        fecha_emision    = timezone.now().date(),
    )

    # ── Crear los detalles de productos ──────────────────────────────────────
    for detalle in pedido.detalle.select_related('producto').all():
        precio_unit = detalle.precio_unitario
        cantidad    = detalle.cantidad
        total_item  = precio_unit * cantidad

        DetalleFactura.objects.create(
            factura          = factura,
            producto         = detalle.producto,
            descripcion      = detalle.producto.nombre,
            codigo_producto  = detalle.producto.codigo,
            cantidad         = cantidad,
            precio_unitario  = precio_unit,
            descuento        = 0,
            total            = total_item,
        )

    # ── 🔥 NUEVO: Agregar costo de delivery como item separado ───────────────
    if pedido.costo_delivery and pedido.costo_delivery > 0:
        producto_delivery = obtener_o_crear_producto_delivery(pedido.costo_delivery)
        
        DetalleFactura.objects.create(
            factura          = factura,
            producto         = producto_delivery,
            descripcion      = "Servicio de Delivery",
            codigo_producto  = producto_delivery.codigo,
            cantidad         = 1,
            precio_unitario  = pedido.costo_delivery,
            total            = pedido.costo_delivery,
        )

    # ── Calcular totales con IVA ─────────────────────────────────────────────
    factura.calcular_totales()

    return factura