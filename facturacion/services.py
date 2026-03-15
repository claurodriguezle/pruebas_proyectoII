"""
facturacion/services.py
───────────────────────
Lógica de negocio para generar facturas desde pedidos.
Importá esta función desde pedidos/views.py al marcar Entregado.
"""

from django.utils import timezone
from decimal import Decimal
from .models import Factura, DetalleFactura, Timbrado


def generar_numero_factura(timbrado):
    """
    Genera el próximo número de factura en formato 001-001-XXXXXXX.
    Busca la última factura del timbrado activo y suma 1.
    """
    ultima = (
        Factura.objects
        .filter(timbrado=timbrado)
        .order_by('-cod_fact')
        .first()
    )

    if ultima:
        # Extraemos el número secuencial de "001-001-0000001"
        try:
            secuencial = int(ultima.nro_fact.split('-')[-1]) + 1
        except (ValueError, IndexError):
            secuencial = 1
    else:
        secuencial = 1

    return f"001-001-{str(secuencial).zfill(7)}"


def generar_factura_desde_pedido(pedido):
    """
    Genera una Factura y sus DetalleFactura a partir de un Pedido.
    Retorna la factura creada, o None si no hay timbrado activo.

    Uso:
        from facturacion.services import generar_factura_desde_pedido
        factura = generar_factura_desde_pedido(pedido)
    """
    # ── Verificar timbrado activo ────────────────────────────────────────────
    timbrado = Timbrado.objects.filter(activo=True, eliminado=False).first()
    if not timbrado:
        return None  # Sin timbrado activo no se puede facturar

    # ── Datos del cliente ────────────────────────────────────────────────────
    persona = pedido.cliente.persona
    ruc_o_ci = persona.ruc if persona.ruc else persona.cedula
    direccion = (
        f"{persona.barrio.nombre}, {persona.ciudad.nombre}"
        if persona.barrio and persona.ciudad
        else ""
    )

    # ── Crear la factura ─────────────────────────────────────────────────────
    nro_fact = generar_numero_factura(timbrado)

    factura = Factura.objects.create(
        nro_fact         = nro_fact,
        pedido = pedido,
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

    # ── Crear los detalles ───────────────────────────────────────────────────
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

    # ── Calcular totales con IVA ─────────────────────────────────────────────
    factura.calcular_totales()

    return factura
