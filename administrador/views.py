from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction, IntegrityError, connection
from django.db.models import Q, Value, CharField
from decimal import Decimal, InvalidOperation
from .models import Persona, Cliente, Empleado, Proveedor, Producto, CategoriaProducto, IngredienteProducto
from .forms import PersonaForm, ProductoForm, CategoriaProductoForm, IngredienteProductoForm, RolForm, EmpleadoForm, ProveedorForm 
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
#Importaciones para Compras
from .models import Compra, DetalleCompra, Item
from .forms import CompraForm
from . import models
from django.utils import timezone
from django.contrib.auth.decorators import login_required
#Importaciones para Stock
from .models import Stock
from django.db.models import Sum
#from . import models {}
from .forms import ItemForm

from django.core.paginator import Paginator


# PERSONAS
def menu(request):
    return render(request, 'administrador/menu.html')

def listar_personas(request):
    grupo = request.GET.get('grupo')  # Captura el grupo seleccionado del select
    search = request.GET.get('search')  # Captura el texto de búsqueda ingresado

    # Inicializamos la variable personas como lista vacía
    personas = []

    # FILTRO POR GRUPO
    if grupo == 'Clientes':
        personas = Cliente.objects.annotate(tipo_persona=Value("Cliente", output_field=CharField()))
    elif grupo == 'Empleados':
        personas = Empleado.objects.annotate(tipo_persona=Value("Empleado", output_field=CharField()))
    elif grupo == 'Proveedores':
        personas = Proveedor.objects.annotate(tipo_persona=Value("Proveedor", output_field=CharField()))
    else:
        # Si no se seleccionó ningún grupo, traemos todos
        personas = list(Cliente.objects.annotate(tipo_persona=Value("Cliente", output_field=CharField())))
        personas += list(Empleado.objects.annotate(tipo_persona=Value("Empleado", output_field=CharField())))
        personas += list(Proveedor.objects.annotate(tipo_persona=Value("Proveedor", output_field=CharField())))

    # FILTRO POR BÚSQUEDA
    if search:
        personas = [
            p for p in personas
            if search.lower() in p.nombre.lower() or search in p.cedula
        ]

    # RENDERIZADO
    if hasattr(request, "htmx") and request.htmx:
        # Si el request viene de HTMX, devolvemos solo el fragmento de tabla (HTMX parcial)
        return render(request, 'administrador/partials/persona_table.html', {'personas': personas})

    # Si es una carga normal, renderizamos toda la página
    return render(request, 'administrador/listar.html', {'personas': personas})

def crear_persona(request):
    if request.method == 'POST':
        persona_form = PersonaForm(request.POST)
        rol_form = RolForm(request.POST)

        empleado_form = None
        proveedor_form = None

        if persona_form.is_valid() and rol_form.is_valid():
            rol = rol_form.cleaned_data['rol']

            if rol == 'empleado':
                empleado_form = EmpleadoForm(request.POST)
                if not empleado_form.is_valid():
                    return render(request, 'administrador/registro.html', {
                        'persona_form': persona_form,
                        'rol_form': rol_form,
                        'empleado_form': empleado_form,
                        'proveedor_form': ProveedorForm(),
                    })
                
            elif rol == 'proveedor':
                proveedor_form = ProveedorForm(request.POST)
                if not proveedor_form.is_valid():
                    return(render, 'administrador/registro.html', {
                        'persona_form': persona_form,
                        'rol_form': rol_form,
                        'empleado_form': EmpleadoForm(),
                        'proveedor_form': proveedor_form,
                    })
                
            with transaction.atomic():
                persona = persona_form.save()

                if rol == 'cliente':
                    Cliente.objects.create(persona=persona)

                elif rol == 'empleado':
                    empleado = empleado_form.save(commit=False)
                    empleado.persona = persona
                    empleado.save()
                
                elif rol == 'proveedor':
                    proveedor = proveedor_form.save(commit=False)
                    proveedor.persona = persona
                    proveedor.save()

            return redirect('administrador:listar_personas')
    else:
        persona_form = PersonaForm()
        rol_form = RolForm()
        empleado_form = EmpleadoForm()
        proveedor_form = ProveedorForm()
    return render(request, 'administrador/registro.html', {
        'persona_form': persona_form,
        'rol_form': rol_form,
        'empleado_form': empleado_form,
        'proveedor_form': proveedor_form,
    })


def editar_persona(request, id):
    persona = get_object_or_404(Persona, id=id)

    rol_principal = None
    if hasattr(persona, 'empleado'):
        rol_principal = 'empleado'
    elif hasattr(persona, 'proveedor'):
        rol_principal = 'proveedor'

    es_cliente = hasattr(persona, 'cliente')

    if request.method == 'POST':
        persona_form = PersonaForm(request.POST, instance=persona)
        rol_form = RolForm(request.POST)

        empleado_form = EmpleadoForm(
            request.POST, instance=getattr(persona, 'empleado', None)
        )
        proveedor_form = ProveedorForm(
            request.POST, instance=getattr(persona, 'proveedor', None)
        )

        rol = request.POST.get('rol')

        forms_validos = (
            persona_form.is_valid() and
            rol_form.is_valid() and (
                empleado_form.is_valid() if rol == 'empleado'
                else proveedor_form.is_valid() if rol == 'proveedor'
                else True
            )
        )

        if forms_validos:
            with transaction.atomic():
                persona_form.save()

                if rol == 'cliente':
                    Cliente.objects.get_or_create(persona=persona)
                    # NO tocar empleado/proveedor

                elif rol == 'empleado':
                    Proveedor.objects.filter(persona=persona).delete()

                    empleado = empleado_form.save(commit=False)
                    empleado.persona = persona
                    empleado.save()

                elif rol == 'proveedor':
                    Empleado.objects.filter(persona=persona).delete()

                    proveedor = proveedor_form.save(commit=False)
                    proveedor.persona = persona
                    proveedor.save()

            return redirect('administrador:listar_personas')

    else:
        persona_form = PersonaForm(instance=persona)
        rol_form = RolForm(initial={'rol': rol_principal})

        empleado_form = EmpleadoForm(instance=getattr(persona, 'empleado', None))
        proveedor_form = ProveedorForm(instance=getattr(persona, 'proveedor', None))

    return render(request, 'administrador/registro.html', {
        'persona_form': persona_form,
        'empleado_form': empleado_form,
        'proveedor_form': proveedor_form,
        'rol_form': rol_form,
        'persona': persona,
        'rol_principal': rol_principal,
        'es_cliente': es_cliente,
    })


def eliminar_persona(request, id):
    persona = get_object_or_404(Persona, id=id)
    persona.delete()
    return redirect('administrador:listar_personas')

# PRODUCTOS
# PAGINA PRINCIPAL
def productos(request):
    return render(request, 'productos/productos.html')

# RENDERIZA LA LISTA DE PRODUCTOS ACTIVOS (estado='A') ORDENADOS POR CÓDIGO
def listar_partial(request):
    productos = Producto.objects.filter(estado='A').order_by('codigo')
    return render(request, 'productos/listar_partial.html', {'productos': productos})

# RENDERIZA EL FORMULARIO VACÍO PARA CREAR UN NUEVO PRODUCTO
def crear_partial(request):
    form = ProductoForm()
    return render(request, 'productos/form_partial.html', {'form': form})

# GUARDA UN NUEVO PRODUCTO DESDE EL FORMULARIO (HTMX POST)
def crear_htmx(request):
    form = ProductoForm(request.POST, request.FILES)
    if form.is_valid():
        producto = form.save()
        return render(request, 'productos/row_partial.html', {'producto': producto})
    # si hay errores, vuelve a renderizar el mismo partial de formulario
    return render(request, 'productos/form_partial.html', {'form': form})

# RENDERIZA EL FORMULARIO CON LOS DATOS DE UN PRODUCTO EXISTENTE PARA EDITAR
def editar_partial(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(instance=producto)
    return render(request, 'productos/form_partial.html', {
        'form': form,
        'producto': producto
    })

# ACTUALIZA UN PRODUCTO EXISTENTE CON LOS DATOS DEL FORMULARIO (HTMX POST)
def editar_htmx(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST, request.FILES, instance=producto)
    if form.is_valid():
        producto = form.save()
        return render(request, 'productos/row_partial.html', {'producto': producto})
    return render(request, 'productos/form_partial.html', {
        'form': form,
        'producto': producto
    })

# ELIMINA UN PRODUCTO Y DEVUELVE UNA RESPUESTA VACÍA PARA QUE HTMX ELIMINE LA FILA EN LA VISTA
def eliminar_htmx(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    return HttpResponse('')

#COMPRAS

def lista_compras(request):
    query = request.GET.get('q', '').strip()
    
    compras = Compra.objects.all().select_related('proveedor').order_by('-fecha')
    
    if query:
        compras = compras.filter(
            Q(numero_factura__icontains=query) |
            Q(proveedor__nombre_empresa__icontains=query) |
            Q(proveedor__nombre__icontains=query) |
            Q(proveedor__apellido__icontains=query)
        )
    
    return render(request, 'compras/lista_compras.html', {
        'compras': compras,
        'query': query
    })

def crear_compra(request):
    UNIDAD_CHOICES = Item.UNIDAD_CHOICES
    TIPO_CHOICES = Item.TIPO_CHOICES

    if request.method == 'POST':
        compra_form = CompraForm(request.POST)
        
        if compra_form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar la compra principal
                    compra = compra_form.save()

                    # Obtener las listas de ítems, cantidades, precios, tipos y unidades
                    items = request.POST.getlist('items')
                    cantidades = request.POST.getlist('cantidades')
                    precios = request.POST.getlist('precios')
                    tipos = request.POST.getlist('tipos')
                    unidades = request.POST.getlist('unidades')

                    # Validaciones básicas
                    if not items or not any(item.strip() for item in items):
                        raise ValidationError("Debe agregar al menos un ítem válido")

                    if len(items) != len(cantidades) or len(items) != len(precios):
                        raise ValidationError("Datos incompletos en los ítems")

                    # Procesar cada ítem
                    for i in range(len(items)):
                        nombre_item = items[i].strip()
                        if not nombre_item:
                            continue

                        try:
                            cantidad = Decimal(cantidades[i])
                            precio = int(precios[i])

                            if cantidad <= 0 or precio <= 0:
                                raise ValidationError(f"Ítem {i+1}: Valores deben ser positivos")

                            # Buscar el item
                            item = Item.objects.get(id=int(items[i]))

                            '''
                            if not item:
                                # Crear el ítem si no existe
                                item = Item.objects.create(
                                    nombre=nombre_item,
                                    tipo=tipos[i],
                                    unidad_medida=unidades[i]
                                )
                                # Crear su stock inicial en 0
                                proveedor = compra.proveedor
                                Stock.objects.create(
                                    item=item,
                                    cant_minima=0,
                                    cant_maxima=0,
                                    cant_disponible=0,
                                    proveedor_principal=proveedor
                                )
                            '''
                            # Conversión de unidades: si es kg, pasar a gramos
                            if unidades[i] == 'kg':
                                precio_por_gramo = precio / 1000
                                cantidad_en_gramos = cantidad * 1000
                            else:
                                precio_por_gramo = precio
                                cantidad_en_gramos = cantidad

                            # Crear detalle de compra
                            DetalleCompra.objects.create(
                                compra=compra,
                                item=item,
                                cantidad=cantidad_en_gramos,
                                precio_compra=precio_por_gramo
                            )

                        except (InvalidOperation, ValueError) as e:
                            raise ValidationError(f"Error en ítem {i+1}: {str(e)}")

                    # Calcular totales y actualizar el stock
                    compra.calcular_totales()
                    actualizar_stock_desde_compra(compra)

                    messages.success(request, '✅ Compra registrada exitosamente!')
                    return redirect('administrador:lista_compras')

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, '❌ Error al guardar la compra')
                print(f"Error: {str(e)}")
        else:
            for field, errors in compra_form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field}: {error}")
    
    # GET Request
    context = {
        'compra_form': CompraForm(),
        'proveedores': Proveedor.objects.all(),
        'unidad_choices': UNIDAD_CHOICES,
        'tipo_choices': TIPO_CHOICES,
        'items_existentes': Item.objects.all(),
    }
    return render(request, 'compras/crear_compra.html', context)

def detalle_compra(request, compra_id):
    compra = get_object_or_404(Compra, pk=compra_id)
    detalles = compra.detalles.all().select_related('item')

    context = {
        'compra':compra,
        'detalles':detalles,
    }
    return render(request,'compras/detalles_compra.html',context)

#Editar Compra
@transaction.atomic
def editar_compra(request, compra_id):
    compra = get_object_or_404(Compra, pk=compra_id)
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1️⃣ Revertir el impacto anterior en el stock
                    for detalle in compra.detalles.all():
                        stock = Stock.objects.filter(item=detalle.item).first()
                        if stock:
                            stock.cant_disponible -= detalle.cantidad
                            if stock.cant_disponible < 0:
                                stock.cant_disponible = 0
                            stock.save()

                    # 2️⃣ Eliminar detalles anteriores
                    compra.detalles.all().delete()

                    # 3️⃣ Guardar la compra con nuevos datos
                    compra = form.save()

                    # 4️⃣ Procesar nuevos ítems
                    items = request.POST.getlist('items')
                    cantidades = request.POST.getlist('cantidades')
                    precios = request.POST.getlist('precios')
                    tipos = request.POST.getlist('tipos')
                    unidades = request.POST.getlist('unidades')

                    for i in range(len(items)):
                        nombre_item = items[i].strip()
                        if not nombre_item:
                            continue

                        try:
                            cantidad = Decimal(cantidades[i])
                            precio = int(precios[i])

                            if cantidad <= 0 or precio <= 0:
                                raise ValidationError(f"Ítem {i+1}: Valores deben ser positivos")

                            # Conversión: si es kg, pasar a gramos
                            if unidades[i] == 'kg':
                                precio_por_gramo = precio / 1000
                                cantidad_en_gramos = cantidad * 1000
                            else:
                                precio_por_gramo = precio
                                cantidad_en_gramos = cantidad

                            # Obtener o crear el ítem
                            item, _ = Item.objects.get_or_create(
                                nombre=nombre_item,
                                defaults={
                                    'tipo': tipos[i],
                                    'unidad_medida': unidades[i]
                                }
                            )

                            # Crear el detalle de compra
                            DetalleCompra.objects.create(
                                compra=compra,
                                item=item,
                                cantidad=cantidad_en_gramos,
                                precio_compra=precio_por_gramo
                            )

                        except (InvalidOperation, ValueError) as e:
                            raise ValidationError(f"Error en ítem {i+1}: {str(e)}")

                    # 5️⃣ Recalcular totales y actualizar stock
                    compra.calcular_totales()
                    actualizar_stock_desde_compra(compra)

                    messages.success(request, '✅ Compra actualizada exitosamente!')
                    return redirect('administrador:detalle_compra', compra_id=compra.id)

            except Exception as e:
                messages.error(request, f'❌ Error al actualizar: {str(e)}')
    else:
        form = CompraForm(instance=compra)

        # Preparar los datos para mostrar en el formulario
        detalles = compra.detalles.all().select_related('item')
        items_data = []

        for detalle in detalles:
            if detalle.item.unidad_medida == 'kg':
                cantidad_mostrar = detalle.cantidad / 1000
                precio_mostrar = detalle.precio_compra * 1000
            else:
                cantidad_mostrar = detalle.cantidad
                precio_mostrar = detalle.precio_compra

            items_data.append({
                'nombre': detalle.item.nombre,
                'tipo': detalle.item.tipo,
                'unidad': detalle.item.unidad_medida,
                'cantidad': float(cantidad_mostrar),
                'precio': int(precio_mostrar)
            })

    context = {
        'compra_form': form,
        'proveedores': proveedores,
        'items_data': items_data,
        'editing': True,
        'compra': compra,
        'unidad_choices': Item.UNIDAD_CHOICES,
        'tipo_choices': Item.TIPO_CHOICES,
        'items_existentes': Item.objects.all().values_list('nombre', flat=True)
    }

    return render(request, 'compras/crear_compra.html', context)

    
    return render(request, 'compras/crear_compra.html', context)
#ELIMINAR COMPRA
def eliminar_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    compra.delete()
    messages.success(request, f'Compra #{compra.numero_factura} eliminada correctamente')
    return redirect('administrador:lista_compras')
#ANULAR COMPRA
def anular_compra(request, compra_id):
    compra = get_object_or_404(Compra, pk=compra_id)
    
    if compra.estado == 'ANULADA':
        messages.warning(request, 'Esta compra ya está anulada')
        return redirect('administrador:detalle_compra', compra_id=compra_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo_anulacion', '').strip()
        
        if not motivo:
            messages.error(request, 'Debe especificar un motivo de anulación')
            return redirect('administrador:detalle_compra', compra_id=compra_id)
        
        try:
            with transaction.atomic():
                # Revertir el stock (esta es la parte crítica)
                for detalle in compra.detalles.all():
                    stock = Stock.objects.filter(item=detalle.item).first()
                    if stock:
                        # Restamos la cantidad (en lugar de sumar)
                        stock.cant_disponible = max(0, stock.cant_disponible - detalle.cantidad)
                        stock.save()
                
                # Marcar como anulada
                compra.estado = 'ANULADA'
                compra.motivo_anulacion = motivo
                compra.fecha_anulacion = timezone.now()
                compra.save()
                
                messages.success(request, '✅ Compra anulada correctamente')
                return redirect('administrador:detalle_compra', compra_id=compra.id)
        
        except Exception as e:
            messages.error(request, f'❌ Error al anular la compra: {str(e)}')
            return redirect('administrador:detalle_compra', compra_id=compra_id)
    
    # Si llega aquí por GET, redirigir a detalles
    return redirect('administrador:detalle_compra', compra_id=compra_id)

#STOCK

#LISTA DE STOCK
def lista_stock(request):
    query = request.GET.get('q', '').strip()
    
    stocks = Stock.objects.all().select_related('item', 'proveedor_principal').order_by('item__nombre')
    
    if query:
        stocks = stocks.filter(
            Q(item__nombre__icontains=query) |
            Q(proveedor_principal__nombre_empresa__icontains=query)
        )
    
    return render(request, 'stock/lista_stock.html', {
        'stocks': stocks,
        'query': query
    })


#CREAR ITEM Y STOCK
@transaction.atomic
def crear_stock(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            #Aplicar estandarizacion antes de guardar
            nombre = Item.estandarizar_nombre(nombre)
            tipo = request.POST.get('tipo')
            unidad_medida = request.POST.get('unidad_medida')
            cant_minima = Decimal(request.POST.get('cant_minima', 0))
            cant_maxima = Decimal(request.POST.get('cant_maxima', 0))
            cant_disponible = Decimal(request.POST.get('cant_disponible', 0))
            proveedor_id = request.POST.get('proveedor')

            if not nombre:
                raise ValidationError("El nombre del ítem es requerido")
            if cant_minima < 0 or cant_maxima < 0 or cant_disponible < 0:
                raise ValidationError("Las cantidades no pueden ser negativas")
            if cant_minima > cant_maxima:
                raise ValidationError("La cantidad mínima no puede ser mayor que la máxima")

            #  Conversión automática si unidad es kg
            if tipo == 'MATERIA_PRIMA' and unidad_medida == 'kg':
                cant_minima = cant_minima * 1000
                cant_maxima = cant_maxima * 1000
                cant_disponible = cant_disponible * 1000

            item, created_item = Item.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'tipo': tipo,
                    'unidad_medida': unidad_medida
                }
            )

            proveedor = None
            if proveedor_id:
                proveedor = Proveedor.objects.get(id=proveedor_id)

            # Si ya existe stock no se debe crear otro
            stock_existente = Stock.objects.filter(item=item).first()

            if stock_existente:
                stock_existente.cant_minima = cant_minima
                stock_existente.cant_maxima = cant_maxima
                stock_existente.cant_disponible = cant_disponible
                stock_existente.proveedor_principal = proveedor
                stock_existente.save()
            else:
                stock = Stock.objects.create(
                    item=item,
                    cant_minima=cant_minima,
                    cant_maxima=cant_maxima,
                    cant_disponible=cant_disponible,
                    proveedor_principal=proveedor
                )

                #Buscar compras anteriores y sumarlas como stock disponible
                cantidad_total_comprada = item.detalles_compra.aggregate(
                    total=Sum('cantidad')
                )['total'] or 0

                stock.cant_disponible = cantidad_total_comprada
                stock.save()


            messages.success(request, '✅ Ítem y stock creados o actualizados exitosamente')
            return redirect('administrador:lista_stock')

        except Exception as e:
            messages.error(request, f'❌ Error al crear o actualizar el ítem: {str(e)}')

    context = {
        'proveedores': Proveedor.objects.all(),
        'unidad_choices': Item.UNIDAD_CHOICES,
        'tipo_choices': Item.TIPO_CHOICES,
        'items_existentes': Item.objects.all().values_list('nombre', flat=True)
    }
    return render(request, 'stock/crear_stock.html', context)


# Mejorar la función de actualización de stock desde compras
def actualizar_stock_desde_compra(compra):
    """Actualiza el stock disponible cuando se registra una compra"""
    with transaction.atomic():
        for detalle_compra in compra.detalles.all():
            cantidad = detalle_compra.cantidad

            # Buscar el stock correspondiente al item
            stock = Stock.objects.filter(item=detalle_compra.item).first()

            if not stock:
                # Crear un stock básico si no existe
                stock = Stock.objects.create(
                    item=detalle_compra.item,
                    cant_minima=0,
                    cant_maxima=0,
                    cant_disponible=0,
                    proveedor_principal=detalle_compra.compra.proveedor
                )

            # Actualizar los datos del stock
            stock.cant_disponible += cantidad
            stock.proveedor_principal = detalle_compra.compra.proveedor
            stock.detalle_compra = detalle_compra
            stock.fecha_ultima_entrada = detalle_compra.compra.fecha
            stock.save()

def ajustar_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    
    if request.method == 'POST':
        cantidad = Decimal(request.POST.get('cantidad', 0))
        
        if cantidad < 0:
            messages.error(request, 'La cantidad no puede ser negativa')
        else:
            stock.cantidad_disponible = cantidad
            stock.save()
            messages.success(request, 'Stock actualizado correctamente')
            return redirect('lista_stock')
    
    return render(request, 'stock/ajustar_stock.html', {'stock': stock})

#Editar Stock 
@transaction.atomic
def editar_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == 'POST':
        try:
            cant_minima = Decimal(request.POST.get('cant_minima', 0))
            cant_maxima = Decimal(request.POST.get('cant_maxima', 0))
            proveedor_id = request.POST.get('proveedor')

            if cant_minima < 0 or cant_maxima < 0:
                raise ValidationError("Las cantidades no pueden ser negativas")
            if cant_minima > cant_maxima:
                raise ValidationError("La cantidad mínima no puede ser mayor que la máxima")

            if stock.item.tipo == 'MATERIA_PRIMA' and stock.item.unidad_medida == 'kg':
                cant_minima = cant_minima * 1000
                cant_maxima = cant_maxima * 1000

            stock.cant_minima = cant_minima
            stock.cant_maxima = cant_maxima
            stock.proveedor_principal = Proveedor.objects.get(id=proveedor_id) if proveedor_id else None
            stock.save()

            messages.success(request, '✅ Stock actualizado correctamente.')
            return redirect('administrador:lista_stock')

        except Exception as e:
            messages.error(request, f'❌ Error al editar el stock: {str(e)}')

    context = {
        'stock': stock,
        'proveedores': Proveedor.objects.all(),
        'tipo_choices': Item.TIPO_CHOICES,
        'unidad_choices': Item.UNIDAD_CHOICES,
        'valores_previos': {
            'nombre': stock.item.nombre,
            'tipo': stock.item.tipo,
            'unidad_medida': stock.item.unidad_medida,
            'cant_minima': stock.cant_minima,
            'cant_maxima': stock.cant_maxima,
            'proveedor': stock.proveedor_principal.id if stock.proveedor_principal else '',
        }
    }
    return render(request, 'stock/crear_stock.html', context)

#Eliminar Stock
@transaction.atomic
def eliminar_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)
    item_nombre = stock.item.nombre
    stock.delete()
    messages.success(request, f'🗑️ Ítem "{item_nombre}" eliminado del stock.')
    return redirect('administrador:lista_stock')


# CATEGORIAS
# PAGINA PRINCIPAL
def categorias(request):
    return render(request, 'categorias/categorias.html')

def crear_categorias(request):
    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST)
        if form.is_valid():
            form.save()
            categorias = CategoriaProducto.objects.all().order_by('nombre_categ')
            html = render_to_string('categorias/partials/lista.html', {'categorias': categorias})
            response = HttpResponse(html)
            response['HX-Trigger'] = 'modalCategoriaCerrado'
            return response
        else:
            return render(request, 'categorias/partials/categoria_form_partial.html', {'form': form})
    else:
        form = CategoriaProductoForm()
        return render(request, 'categorias/partials/categoria_form_partial.html', {'form': form})

def listar_categorias_partial(request):
    categorias = CategoriaProducto.objects.all().order_by('nombre_categ')
    return render(request, 'categorias/partials/lista.html', {'categorias': categorias})

def eliminar_categoria(request, pk):
    if request.method == 'DELETE':
        try:
            categoria = CategoriaProducto.objects.get(pk=pk)
            categoria.delete()
            categorias = CategoriaProducto.objects.all()
            return render(request, 'categorias/partials/lista.html', {'categorias': categorias})
        except CategoriaProducto.DoesNotExist:
            raise Http404('Categoría no encontrada')

def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)

    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            categorias = CategoriaProducto.objects.all().order_by('nombre_categ')
            html = render_to_string('categorias/partials/lista.html', {'categorias': categorias})
            response = HttpResponse(html)
            response['HX-Trigger'] = 'modalCategoriaCerrado'
            return response
        else:
            return render(request, 'categorias/partials/categoria_form_partial.html', {'form': form, 'categoria': categoria})
    else:
        form = CategoriaProductoForm(instance=categoria)
        return render(request, 'categorias/partials/categoria_form_partial.html', {'form': form, 'categoria': categoria})

# INGREDIENTES DE PRODUCTOS

# OBTENEMOS LA PAGINA PRINCIPAL
def ingredientes(request, id):
    producto = get_object_or_404(Producto, id=id)
    ingredientes = IngredienteProducto.objects.filter(producto=producto)

    tipo = producto.categoria.tipo if producto.categoria else 'ingrediente'
    label_item = 'Artículo' if tipo == 'articulo' else 'Ingrediente'

    return render(request, 'ingredientes/ingredientes.html',{
        'producto': producto,
        'ingredientes': ingredientes,
        'label_item': label_item,
    })

# TRAE LOS ITEM DE LA BD Y LOS MUESTRA EN EL SELECT DEL FORM
def cargar_items(request):
    items = Item.objects.all()

    return render(request, 'ingredientes/partials/select_items.html', {
        "items": items,
    })

# GUARDA LOS INGREDIENTES
def agregar_ingredientes(request, producto_id):
    if request.method == 'POST':

        producto = get_object_or_404(Producto, pk=producto_id)

        item_id = request.POST.get('item')
        cantidad = request.POST.get('cantidad')

        if not item_id or not cantidad:
            return HttpResponseBadRequest('Faltan datos')
        
        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            return HttpResponseBadRequest('Ingrediente inválido')
        
        #ingrediente = IngredienteProducto(producto=producto, item=item, cantidad=cantidad)
        #ingrediente.save()

        IngredienteProducto.objects.create(producto=producto, item=item, cantidad=cantidad)

        ingredientes = IngredienteProducto.objects.filter(producto=producto)

        return render(request, 'ingredientes/partials/lista_ingredientes.html', {'ingredientes': ingredientes})
    return HttpResponseBadRequest("Petición inválida")

# LISTAR TODOS LOS INGREDIENTES
def listar_ingredientes(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    ingredientes = IngredienteProducto.objects.filter(producto=producto)
    return render(request, 'ingredientes/partials/lista_ingredientes.html', {
        'ingredientes': ingredientes
    })

# ELIMINAR INGREDIENTE
def eliminar_ingrediente(request, pk):
    if request.method == 'DELETE':
        try:
            ingrediente = IngredienteProducto.objects.get(pk=pk)
            producto_id = ingrediente.producto.id
            ingrediente.delete()
            ingredientes = IngredienteProducto.objects.filter(producto_id=producto_id)
            return render(request, 'ingredientes/partials/lista_ingredientes.html', {
                'ingredientes': ingredientes
            })
        except IngredienteProducto.DoesNotExist:
            raise Http404('El ingrediente no se encontró.')
        
# VISTA PARA MOSTRAR EL FORM DE EDICION(INLINE)
def editar_ingrediente_form(request, pk):
    ingrediente = get_object_or_404(IngredienteProducto, pk=pk)
    return render(request, 'ingredientes/partials/editar_fila_ingrediente.html', {'ingrediente': ingrediente})

# ACTUALIZA CANTIDAD DE INGREDIENTE
@require_POST
def actualizar_ingrediente(request, pk):
    ingrediente = get_object_or_404(IngredienteProducto, pk=pk)
    cantidad = request.POST.get('cantidad')

    if not cantidad:
        return HttpResponseBadRequest('Cantidad faltante')
    
    ingrediente.cantidad = cantidad
    ingrediente.save()

    return render(request, 'ingredientes/partials/fila_ingrediente.html', {'ingrediente': ingrediente})

# Renderiza la fila al cancelar la edicion inline 
def ver_fila_ingrediente(request, pk):
    ingrediente = get_object_or_404(IngredienteProducto, pk=pk)
    return render(request, 'ingredientes/partials/fila_ingrediente.html', {'ingrediente': ingrediente})

#ITEMS
def lista_items(request):
    query = request.GET.get('q', '').strip()

    items = Item.objects.all().order_by('nombre')

    if query:
        items = items.filter(
            Q(nombre__icontains=query)
        )

    return render(request, 'items/lista_items.html', {
        'items': items,
        'query': query
    })

def editar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        # Procesar el formulario cuando se envía
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ítem actualizado correctamente')
            return redirect('administrador:lista_items')
    else:
        # Mostrar el formulario con datos actuales
        form = ItemForm(instance=item)
    
    # Preparamos los datos para el template
    valores_previos = {
        'nombre': item.nombre,
        'tipo': item.tipo,
        'unidad_medida': item.unidad_medida,
        # No incluimos datos de stock aquí
    }
    
    return render(request, 'stock/crear_stock.html', {
        'modo_edicion': True,  # Flag clave para el template
        'valores_previos': valores_previos,
        'tipo_choices': Item.TIPO_CHOICES,
        'unidad_choices': Item.UNIDAD_CHOICES,
        'proveedores': Proveedor.objects.all()
    })

def eliminar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Ítem eliminado correctamente')
        return redirect('administrador:lista_items')
    
    return render(request, 'items/eliminar_item.html', {
        'item': item
    })