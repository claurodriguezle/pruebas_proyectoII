from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, F
from django.utils.dateparse import parse_date
from datetime import date
import calendar
from decimal import Decimal, ROUND_HALF_UP
from django.db.models.functions import TruncDate
from django.db.models.functions import ExtractWeekDay

from facturacion.models import DetalleFactura, Factura
from administrador.models import Item, DetalleCompra, Producto, IngredienteProducto, CategoriaProducto


def _get_datos_reporte(fecha_inicio, fecha_fin, categoria_id=None):

    # Retorna los datos de ventas por producto en el rango de fechas dado.
    # Si categoria_id es None, trae todos los productos.

    qs = DetalleFactura.objects.filter(
        factura__fecha_emision__range=(fecha_inicio, fecha_fin)
    )

    if categoria_id:
        qs = qs.filter(producto__categoria_id=categoria_id)

    datos = (
        qs
        .values(
            'producto__codigo',
            'producto__nombre',
            'producto__categoria__nombre_categ', 
        )
        .annotate(
            total_unidades=Sum('cantidad'),
            total_ingresos=Sum('total'),
        )
        .order_by('-total_unidades')
    )

    return list(datos)


def reporte_ventas_productos(request):
    # Vista principal del reporte. Renderiza el template con filtros

    categorias = CategoriaProducto.objects.all().order_by('nombre_categ')

    # Categoría por defecto: buscar "Hamburguesas" si existe
    categoria_default = categorias.filter(nombre_categ__icontains='hamburguesa').first()

    # Fechas por defecto: mes actual
    hoy = date.today()
    fecha_inicio_default = hoy.replace(day=1)
    fecha_fin_default = hoy

    context = {
        'categorias': categorias,
        'categoria_default': categoria_default,
        'fecha_inicio_default': fecha_inicio_default.strftime('%Y-%m-%d'),
        'fecha_fin_default': fecha_fin_default.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/ventas_productos.html', context)


def reporte_ventas_productos_datos(request):
    
    # Endpoint HTMX que retorna el HTML parcial con los resultados del reporte.
    # Se invoca al aplicar filtros desde el frontend.

    # Leer parámetros 
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    categoria_id = request.GET.get('categoria') or None

    # Validar y parsear fechas
    hoy = date.today()
    fecha_inicio = parse_date(fecha_inicio_str) if fecha_inicio_str else hoy.replace(day=1)
    fecha_fin = parse_date(fecha_fin_str) if fecha_fin_str else hoy

    if not fecha_inicio or not fecha_fin:
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy

    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    #  Obtener datos 
    datos = _get_datos_reporte(fecha_inicio, fecha_fin, categoria_id)

    total_unidades = sum(d['total_unidades'] for d in datos)
    total_ingresos = sum(d['total_ingresos'] for d in datos)
    cantidad_productos = len(datos)

    for d in datos:
        d['participacion'] = (
            round((d['total_unidades'] / total_unidades) * 100, 1)
            if total_unidades > 0 else 0
        )
        d['max_unidades'] = datos[0]['total_unidades'] if datos else 1

    mas_vendido = datos[0] if datos else None
    menos_vendido = datos[-1] if len(datos) > 1 else None

    context = {
        'datos': datos,
        'total_unidades': total_unidades,
        'total_ingresos': total_ingresos,
        'cantidad_productos': cantidad_productos,
        'mas_vendido': mas_vendido,
        'menos_vendido': menos_vendido,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'sin_resultados': len(datos) == 0,
    }

    return render(request, 'reportes/partials/ventas_productos_resultados.html', context)

# REPORTE: DELIVERY VS RETIRO

def reporte_entregas(request):
    #Vista principal del reporte de tipos de entrega
    hoy = date.today()
    context = {
        'fecha_inicio_default': hoy.replace(day=1).strftime('%Y-%m-%d'),
        'fecha_fin_default': hoy.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/entregas.html', context)

def reporte_entregas_datos(request):
    #Endpoint HTMX que retorna el partial con los resultados
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str    = request.GET.get('fecha_fin')

    hoy = date.today()
    fecha_inicio = parse_date(fecha_inicio_str) if fecha_inicio_str else hoy.replace(day=1)
    fecha_fin    = parse_date(fecha_fin_str)    if fecha_fin_str    else hoy

    if not fecha_inicio or not fecha_fin:
        fecha_inicio = hoy.replace(day=1)
        fecha_fin    = hoy

    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

    # Query: facturas con pedido asociado, agrupadas por tipo_entrega
    from django.db.models import Count, Sum

    qs = (
        Factura.objects
        .filter(
            pedido__isnull=False,
            fecha_emision__range=(fecha_inicio, fecha_fin)
        )
        .values('pedido__tipo_entrega')
        .annotate(
            total_pedidos=Count('cod_fact'),
            total_facturado=Sum('monto_total'),
        )
    )

    # Mapear códigos a etiquetas legibles
    etiquetas = {'RE': 'Retiro en local', 'DE': 'Delivery'}
    datos = []
    for row in qs:
        codigo = row['pedido__tipo_entrega']
        datos.append({
            'codigo': codigo,
            'etiqueta': etiquetas.get(codigo, codigo),
            'total_pedidos': row['total_pedidos'],
            'total_facturado': row['total_facturado'] or 0,
        })

    # Ordenar: Retiro primero, Delivery segundo
    datos.sort(key=lambda x: x['codigo'], reverse=True)

    total_pedidos   = sum(d['total_pedidos']   for d in datos)
    total_facturado = sum(d['total_facturado'] for d in datos)

    # Agregar porcentaje
    for d in datos:
        d['porcentaje'] = (
            round((d['total_pedidos'] / total_pedidos) * 100, 1)
            if total_pedidos > 0 else 0
        )

    context = {
        'datos': datos,
        'total_pedidos': total_pedidos,
        'total_facturado': total_facturado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'sin_resultados': len(datos) == 0,
    }
    return render(request, 'reportes/partials/entregas_resultados.html', context)

# REPORTE DE TOP 10 CLIENTES
def reporte_top_clientes(request):
    #Vista principal del reporte de top clientes
    hoy = date.today()
    context = {
        'fecha_inicio_default': hoy.replace(day=1).strftime('%Y-%m-%d'),
        'fecha_fin_default': hoy.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/top_clientes.html', context)
 
def reporte_top_clientes_datos(request):
    #Endpoint HTMX con los resultados del reporte
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str    = request.GET.get('fecha_fin')
 
    hoy = date.today()
    fecha_inicio = parse_date(fecha_inicio_str) if fecha_inicio_str else hoy.replace(day=1)
    fecha_fin    = parse_date(fecha_fin_str)    if fecha_fin_str    else hoy
 
    if not fecha_inicio or not fecha_fin:
        fecha_inicio = hoy.replace(day=1)
        fecha_fin    = hoy
 
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
 
    from django.db.models import Count, Sum

    datos = list(
    Factura.objects
    .filter(fecha_emision__range=(fecha_inicio, fecha_fin))
    .exclude(cliente__persona__cedula='0000000')  # excluir cliente ocasional
    .values(
        'cliente__persona__nombre',
        'cliente__persona__apellido',
    )
    .annotate(
        total_compras=Count('cod_fact'),
        total_facturado=Sum('monto_total'),
    )
    .order_by('-total_facturado')[:10]
    )

    total_facturado_general = sum(d['total_facturado'] or 0 for d in datos)
 
    # Agregar porcentaje sobre el total del top 10
    for d in datos:
        d['total_facturado'] = d['total_facturado'] or 0
        d['porcentaje'] = (
            round((d['total_facturado'] / total_facturado_general) * 100, 1)
            if total_facturado_general > 0 else 0
        )
        d['nombre_completo'] = f"{d['cliente__persona__nombre']} {d['cliente__persona__apellido']}"
 
    context = {
        'datos': datos,
        'total_facturado_general': total_facturado_general,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'sin_resultados': len(datos) == 0,
    }
    return render(request, 'reportes/partials/top_clientes_resultados.html', context)

# REPORTES DE VENTAS
def reporte_ventas(request):
    #Vista principal del reporte de ventas
    hoy = date.today()
    context = {
        'fecha_inicio_default': hoy.replace(day=1).strftime('%Y-%m-%d'),
        'fecha_fin_default': hoy.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/ventas.html', context)

def reporte_ventas_datos(request):
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str    = request.GET.get('fecha_fin')
 
    hoy = date.today()
    fecha_inicio = parse_date(fecha_inicio_str) if fecha_inicio_str else hoy.replace(day=1)
    fecha_fin    = parse_date(fecha_fin_str)    if fecha_fin_str    else hoy
 
    if not fecha_inicio or not fecha_fin:
        fecha_inicio = hoy.replace(day=1)
        fecha_fin    = hoy
 
    if fecha_inicio > fecha_fin:
        fecha_inicio, fecha_fin = fecha_fin, fecha_inicio
 
    qs = list(
        Factura.objects
        .filter(fecha_emision__range=(fecha_inicio, fecha_fin))
        .annotate(dia_semana=ExtractWeekDay('fecha_emision'))
        .exclude(dia_semana=2)
        .values('dia_semana')
        .annotate(
            cantidad_facturas=Count('cod_fact'),
            total_facturado=Sum('monto_total'),
        )
        .order_by('dia_semana')
    )
 
    NOMBRES_DIA = {
        1: 'Domingo', 2: 'Lunes', 3: 'Martes',
        4: 'Miércoles', 5: 'Jueves', 6: 'Viernes', 7: 'Sábado',
    }
 
    total_facturado = sum(d['total_facturado'] or 0 for d in qs)
    total_facturas  = sum(d['cantidad_facturas'] for d in qs)
    promedio_diario = round(total_facturado / len(qs)) if qs else 0
 
    max_facturado = max((d['total_facturado'] or 0 for d in qs), default=0)
    min_facturado = min((d['total_facturado'] or 0 for d in qs), default=0)
 
    desglose = []
    for d in qs:
        facturado = d['total_facturado'] or 0
        desglose.append({
            'nombre_dia': NOMBRES_DIA.get(d['dia_semana'], '—'),
            'cantidad_facturas': d['cantidad_facturas'],
            'total_facturado': facturado,
            'porcentaje': round((facturado / total_facturado) * 100, 1) if total_facturado > 0 else 0,
            'es_mejor': facturado == max_facturado and facturado > 0,
            'es_flojo': facturado == min_facturado and len(qs) > 1,
        })
 
    context = {
        'desglose': desglose,
        'total_facturado': total_facturado,
        'total_facturas': total_facturas,
        'promedio_diario': promedio_diario,
        'nombre_dias': desglose,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'sin_resultados': len(desglose) == 0,
    }
    return render(request, 'reportes/partials/ventas_resultados.html', context)

# REPORTES DE COSTOS
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
 
 
def reporte_costos(request):
    """Vista principal del reporte de costos mensuales."""
    hoy = date.today()
    context = {
        'mes_default': hoy.month,
        'anio_default': hoy.year,
        'anios_disponibles': list(range(hoy.year, hoy.year - 5, -1)),
        'meses': [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
        ],
    }
    return render(request, 'reportes/costos.html', context)
 
 
def reporte_costos_datos(request):
    """Partial HTMX con los datos del reporte de costos del período."""
    hoy = date.today()
 
    try:
        mes = int(request.GET.get('mes', hoy.month))
        anio = int(request.GET.get('anio', hoy.year))
    except (ValueError, TypeError):
        mes = hoy.month
        anio = hoy.year
 
    if mes < 1 or mes > 12:
        mes = hoy.month
    if anio < 2000 or anio > hoy.year:
        anio = hoy.year
 
    # Rango del mes seleccionado
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_inicio = date(anio, mes, 1)
    fecha_fin = date(anio, mes, ultimo_dia)
 
    # CPP acumulado hasta el último día del mes
    cpp_dict = calcular_cpp_por_item(hasta_fecha=fecha_fin)
 
    # Detalles de factura del mes agrupados por producto
    detalles = (
        DetalleFactura.objects
        .filter(factura__fecha_emision__range=(fecha_inicio, fecha_fin))
        .values('producto')
        .annotate(
            cant_vendida=Sum('cantidad'),
            total_vendido=Sum('total'),
        )
        .order_by('producto__categoria__nombre_categ', 'producto__nombre')
    )
 
    # Precargar todos los productos involucrados de una sola query
    producto_ids = [d['producto'] for d in detalles]
    productos_map = {
        p.pk: p for p in Producto.objects.filter(pk__in=producto_ids)
        .prefetch_related('ingredientes__item')
        .select_related('categoria')
    }
 
    MARGEN_CRITICO = 30
 
    filas = []
    for d in detalles:
        producto = productos_map.get(d['producto'])
        if not producto:
            continue
 
        cant_vendida = d['cant_vendida'] or 0
        total_vendido = d['total_vendido'] or 0
 
        costo_unit = calcular_costo_producto(producto, cpp_dict)
        costo_total = int(costo_unit * cant_vendida)
        margen_gs = total_vendido - costo_total
 
        if total_vendido > 0:
            margen_pct = float(
                (Decimal(str(margen_gs)) / Decimal(str(total_vendido)) * 100)
                .quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            )
        else:
            margen_pct = 0.0
 
        filas.append({
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre_categ if producto.categoria else '—',
            'cant_vendida': cant_vendida,
            'costo_unit': int(costo_unit),
            'costo_total': costo_total,
            'total_vendido': total_vendido,
            'margen_gs': margen_gs,
            'margen_pct': margen_pct,
            'margen_critico': margen_pct < MARGEN_CRITICO,
        })
 
    sin_resultados = len(filas) == 0
 
    if not sin_resultados:
        costo_total_general = sum(f['costo_total'] for f in filas)
        total_vendido_general = sum(f['total_vendido'] for f in filas)
        margen_gs_general = total_vendido_general - costo_total_general
        margen_pct_general = round(
            (margen_gs_general / total_vendido_general * 100), 1
        ) if total_vendido_general > 0 else 0
        producto_mas_costoso = max(filas, key=lambda x: x['costo_total'])
        criticos = sum(1 for f in filas if f['margen_critico'])
    else:
        costo_total_general = 0
        total_vendido_general = 0
        margen_gs_general = 0
        margen_pct_general = 0
        producto_mas_costoso = None
        criticos = 0
 
    NOMBRES_MES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
    }
 
    context = {
        'filas': filas,
        'sin_resultados': sin_resultados,
        'costo_total_general': costo_total_general,
        'total_vendido_general': total_vendido_general,
        'margen_gs_general': margen_gs_general,
        'margen_pct_general': margen_pct_general,
        'producto_mas_costoso': producto_mas_costoso,
        'criticos': criticos,
        'margen_critico_umbral': MARGEN_CRITICO,
        'mes': mes,
        'anio': anio,
        'nombre_mes': NOMBRES_MES.get(mes, ''),
    }
    return render(request, 'reportes/partials/costos_resultados.html', context)