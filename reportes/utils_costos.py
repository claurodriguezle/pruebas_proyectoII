from django.db.models import Sum, F, Q
from decimal import Decimal, ROUND_HALF_UP
from administrador.models import DetalleCompra, Producto
from facturacion.models import DetalleFactura
from django.utils import timezone

def calcular_cpp_por_item(hasta_fecha=None):
    """
    Calcula el Costo Promedio Ponderado (CPP) por item.
    Solo considera compras ACTIVAS.
    Si se pasa hasta_fecha, solo considera compras hasta esa fecha (inclusive).
    Retorna un dict: { item_id: cpp_valor (Decimal) }
    """
    qs = DetalleCompra.objects.filter(compra__estado='ACTIVA')

    if hasta_fecha:
        qs = qs.filter(compra__fecha__lte=hasta_fecha)

    datos = (
        qs.values('item_id')
        .annotate(
            suma_ponderada=Sum(F('precio_compra') * F('cantidad')),
            suma_cantidad=Sum('cantidad'),
        )
    )

    cpp = {}
    for d in datos:
        if d['suma_cantidad'] and d['suma_cantidad'] > 0:
            cpp[d['item_id']] = (
                Decimal(str(d['suma_ponderada'])) / Decimal(str(d['suma_cantidad']))
            )
        else:
            cpp[d['item_id']] = Decimal('0')

    return cpp


def calcular_costo_producto(producto, cpp_dict):
    """
    Calcula el costo unitario de producción de un producto
    en base a sus ingredientes y el CPP de cada item.
    Retorna el costo como Decimal redondeado a entero.
    """
    costo = Decimal('0')
    for ing in producto.ingredientes.select_related('item').all():
        cpp_item = cpp_dict.get(ing.item_id, Decimal('0'))
        costo += Decimal(str(ing.cantidad)) * cpp_item

    return costo.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def cpp_display(item, cpp_dict):
    """
    Devuelve el CPP de un item correctamente convertido según su unidad de medida.
    - Materia prima en kg: el CPP se almacena por gramo, se muestra por kg
    - Artículos: CPP por unidad
    Retorna un entero listo para mostrar.
    """
    cpp = cpp_dict.get(item.id, Decimal('0'))

    if item.tipo == 'MATERIA_PRIMA' and item.unidad_medida == 'kg':
        cpp = cpp * 1000  # convertir de gs/gramo a gs/kg

    return int(cpp.quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def calcular_costo_ventas_caja(caja, fecha_referencia=None):
    """
    Calcula el costo total (CPP) de los productos vendidos en una caja específica.
    Contempla dos caminos hacia la caja porque en las facturas generadas
    desde pedidos online, Factura.venta_caja queda en None (bug conocido);
    en ese caso se llega igual vía Factura.pedido.venta_caja.
    """
    if fecha_referencia is None:
        fecha_referencia = timezone.now().date()

    cpp_dict = calcular_cpp_por_item(hasta_fecha=fecha_referencia)

    detalles = (
        DetalleFactura.objects
        .filter(
            Q(factura__venta_caja__caja=caja, factura__venta_caja__anulado=False)
            | Q(factura__pedido__venta_caja__caja=caja, factura__pedido__venta_caja__anulado=False)
        )
        .distinct()
        .values('producto')
        .annotate(cant_vendida=Sum('cantidad'))
    )

    producto_ids = [d['producto'] for d in detalles]
    productos_map = {
        p.pk: p for p in Producto.objects.filter(pk__in=producto_ids)
        .prefetch_related('ingredientes__item')
        .select_related('categoria')
    }

    costo_total = 0
    for d in detalles:
        producto = productos_map.get(d['producto'])
        if not producto:
            continue
        costo_unit = calcular_costo_producto(producto, cpp_dict)
        costo_total += int(costo_unit * (d['cant_vendida'] or 0))

    return costo_total