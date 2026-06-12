from django.db.models import Sum, F
from decimal import Decimal, ROUND_HALF_UP
from administrador.models import DetalleCompra


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