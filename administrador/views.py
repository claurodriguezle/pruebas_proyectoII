from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction, IntegrityError, connection
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from .models import Persona, Cliente, Empleado, Proveedor, Producto, CategoriaProducto
from .forms import PersonaForm, ProductoForm, CategoriaProductoForm 
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
#Importaciones para Compras
from .models import Compra, DetalleCompra, Item
from .forms import CompraForm
#from . import models 


# PERSONAS
def menu(request):
    return render(request, 'administrador/menu.html')

def listar_personas(request):
    personas = Persona.objects.all()
    return render(request, 'administrador/listar.html', {
        'personas': personas
    })

def crear_persona(request):
    if request.method == 'POST':
        print(request.POST)
        form = PersonaForm(request.POST)
        if form.is_valid():
            tipo_persona = form.cleaned_data['tipo_persona']
            persona_data = {
                'nombre': form.cleaned_data['nombre'],
                'apellido': form.cleaned_data['apellido'],
                'telefono': form.cleaned_data['telefono'],
                'email': form.cleaned_data['email'],
                'fecha_nacimiento': form.cleaned_data['fecha_nacimiento'],
                'cedula': form.cleaned_data['cedula'],
                'ciudad': form.cleaned_data['ciudad'],
                'barrio': form.cleaned_data['barrio'],
                'nacionalidad': form.cleaned_data['nacionalidad'],
            }

            try:
                if tipo_persona == 'cliente':
                    # cleaned_data['ruc'] ya será None si está vacío (gracias al form.clean())
                    Cliente.objects.create(**persona_data, ruc=form.cleaned_data['ruc'])

                elif tipo_persona == 'empleado':
                    Empleado.objects.create(
                        **persona_data,
                        sueldo=form.cleaned_data['sueldo'],         # No será None (campo requerido para empleado)
                        fecha_contratacion=form.cleaned_data['fecha_contratacion'],
                        t_empleado=form.cleaned_data['t_empleado']
                    )

                elif tipo_persona == 'proveedor':
                    Proveedor.objects.create(
                        **persona_data,
                        nombre_empresa=form.cleaned_data['nombre_empresa'],
                        ruc=form.cleaned_data['ruc']                # None o valor valido
                    )

                return redirect('administrador:listar_personas')

            except IntegrityError as e:
                # Maneja errores de unicidad
                form.add_error(None, "Error al guardar. Verifica los datos únicos.")
                print(f"Error de integridad: {e}")

    else:
        form = PersonaForm()

    return render(request, 'administrador/registro.html', {'form': form})


def editar_persona(request, id):
    persona = get_object_or_404(Persona, id=id)
    
    # Determinar tipo de persona
    if hasattr(persona, 'cliente'):
        tipo_persona = 'cliente'
        instancia_especifica = persona.cliente
    elif hasattr(persona, 'empleado'):
        tipo_persona = 'empleado'
        instancia_especifica = persona.empleado
    elif hasattr(persona, 'proveedor'):
        tipo_persona = 'proveedor'
        instancia_especifica = persona.proveedor
    else:
        raise Http404("Tipo de persona no válido")

    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Actualización directa vía SQL (bypass ORM)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE administrador_persona SET
                                nombre = %s,
                                apellido = %s,
                                telefono = %s,
                                email = %s,
                                fecha_nacimiento = %s,
                                cedula = %s,
                                ciudad = %s,
                                barrio = %s,
                                nacionalidad = %s
                            WHERE id = %s
                            """,
                            [
                                form.cleaned_data['nombre'],
                                form.cleaned_data['apellido'],
                                form.cleaned_data['telefono'],
                                form.cleaned_data['email'],
                                form.cleaned_data['fecha_nacimiento'],
                                form.cleaned_data['cedula'],
                                form.cleaned_data['ciudad'],
                                form.cleaned_data['barrio'],
                                form.cleaned_data['nacionalidad'],
                                id
                            ]
                        )
                        
                        # Actualización modelo hijo
                        if tipo_persona == 'cliente':
                            cursor.execute(
                                "UPDATE administrador_cliente SET ruc = %s WHERE persona_ptr_id = %s",
                                [form.cleaned_data.get('ruc'), id]
                            )
                        elif tipo_persona == 'empleado':
                            cursor.execute(
                                """UPDATE administrador_empleado SET
                                    sueldo = %s,
                                    fecha_contratacion = %s,
                                    t_empleado = %s
                                WHERE persona_ptr_id = %s""",
                                [
                                    form.cleaned_data['sueldo'],
                                    form.cleaned_data['fecha_contratacion'],
                                    form.cleaned_data['t_empleado'],
                                    id
                                ]
                            )
                        elif tipo_persona == 'proveedor':
                            cursor.execute(
                                """UPDATE administrador_proveedor SET
                                    nombre_empresa = %s,
                                    ruc = %s
                                WHERE persona_ptr_id = %s""",
                                [
                                    form.cleaned_data['nombre_empresa'],
                                    form.cleaned_data.get('ruc'),
                                    id
                                ]
                            )

                    # Forzar recarga de instancias
                    persona.refresh_from_db()
                    if hasattr(persona, 'cliente'):
                        persona.cliente.refresh_from_db()
                    elif hasattr(persona, 'empleado'):
                        persona.empleado.refresh_from_db()
                    elif hasattr(persona, 'proveedor'):
                        persona.proveedor.refresh_from_db()

                return redirect('administrador:listar_personas')
                
            except Exception as e:
                print(f"ERROR EN TRANSACCIÓN: {str(e)}")
                form.add_error(None, f"Error crítico al actualizar: {str(e)}")
    else:
        # CÓDIGO INICIAL DEL FORM (ELSE)
        initial_data = {
            'tipo_persona': tipo_persona,
            'nombre': persona.nombre,
            'apellido': persona.apellido,
            'telefono': persona.telefono,
            'email': persona.email,
            'fecha_nacimiento': persona.fecha_nacimiento,
            'cedula': persona.cedula,
            'ciudad': persona.ciudad,
            'barrio': persona.barrio,
            'nacionalidad': persona.nacionalidad,
            'ruc': getattr(instancia_especifica, 'ruc', None),
            'sueldo': getattr(instancia_especifica, 'sueldo', ''),
            'fecha_contratacion': getattr(instancia_especifica, 'fecha_contratacion', ''),
            't_empleado': getattr(instancia_especifica, 't_empleado', ''),
            'nombre_empresa': getattr(instancia_especifica, 'nombre_empresa', ''),
        }
        form = PersonaForm(initial=initial_data)

    return render(request, 'administrador/registro.html', {
        'form': form,
        'persona': persona,
        'tipo_persona': tipo_persona
    })

def eliminar_persona(request, id):
    persona = get_object_or_404(Persona, id=id)
    persona.delete()
    return redirect('administrador:listar_personas')

# PRODUCTOS

def productos(request):
    return render(request, 'productos/productos.html')

def listar_partial(request):
    productos = Producto.objects.filter(estado='A').order_by('codigo')
    return render(request, 'productos/listar_partial.html', {'productos': productos})

def crear_partial(request):
    form = ProductoForm()
    return render(request, 'productos/form_partial.html', {'form': form})

def crear_htmx(request):
    form = ProductoForm(request.POST, request.FILES)
    if form.is_valid():
        producto = form.save()
        return render(request, 'productos/row_partial.html', {'producto': producto})
    # si hay errores, vuelve a renderizar el mismo partial de formulario
    return render(request, 'productos/form_partial.html', {'form': form})

def editar_partial(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(instance=producto)
    return render(request, 'productos/form_partial.html', {
        'form': form,
        'producto': producto
    })

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
        print("Datos POST recibidos:", request.POST)  # Para depuración

        # 1. Procesar formulario base
        compra_form = CompraForm(request.POST)
        
        if compra_form.is_valid():
            try:
                with transaction.atomic():
                    # 2. Guardar compra principal
                    compra = compra_form.save()

                    # 3. Procesar ítems dinámicos
                    items = request.POST.getlist('items')
                    cantidades = request.POST.getlist('cantidades')
                    precios = request.POST.getlist('precios')
                    tipos = request.POST.getlist('tipos')
                    unidades = request.POST.getlist('unidades')

                    # Validación mejorada
                    if not items or not any(item.strip() for item in items):
                        raise ValidationError("Debe agregar al menos un ítem válido")

                    if len(items) != len(cantidades) or len(items) != len(precios):
                        raise ValidationError("Datos incompletos en los ítems")

                    for i in range(len(items)):
                        nombre_item = items[i].strip()
                        if not nombre_item:
                            continue

                        try:
                            # Conversión y validación
                            cantidad = Decimal(cantidades[i])
                            precio = int(precios[i])

                            if cantidad <= 0 or precio <= 0:
                                raise ValidationError(f"Ítem {i+1}: Valores deben ser positivos")

                            # Conversión de unidades
                            if unidades[i] == 'kg':
                                #Precio ingresado es por kg, convertimos a precio por gramo
                                precio_por_gramo = precio/1000
                                cantidad_en_gramos = cantidad * 1000
                            else:
                                #Precio ya esta en gramos (u otras unidades)
                                precio_por_gramo = precio
                                cantidad_en_gramos = cantidad

                            # Buscar/crear ítem
                            item, _ = Item.objects.get_or_create(
                                nombre=nombre_item,
                                defaults={
                                    'tipo': tipos[i],
                                    'unidad_medida': unidades[i] #Guardamos la unidad original
                                }
                            )

                            # Crear detalle de compra
                            DetalleCompra.objects.create(
                                compra=compra,
                                item=item,
                                cantidad=cantidad_en_gramos, #Siempre en gramos
                                precio_compra=precio_por_gramo #Precio por gramo
                            )

                        except (InvalidOperation, ValueError) as e:
                            raise ValidationError(f"Error en ítem {i+1}: {str(e)}")

                    # Actualizar totales
                    compra.calcular_totales()
                    messages.success(request, '✅ Compra registrada exitosamente!')
                    return redirect('administrador:lista_compras')

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, '❌ Error al guardar la compra')
                print(f"Error: {str(e)}")  # Log detallado
        else:
            for field, errors in compra_form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field}: {error}")
    
    # GET request
    context = {
        'compra_form': CompraForm(),
        'proveedores': Proveedor.objects.all(),
        'unidad_choices': UNIDAD_CHOICES,
        'tipo_choices': TIPO_CHOICES,
        'items_existentes': Item.objects.all().values_list('nombre', flat=True)
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
def editar_compra(request, compra_id):
    compra = get_object_or_404(Compra, pk=compra_id)
    proveedores = Proveedor.objects.all()  # Asegurarnos de pasar los proveedores
    
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            try:
                with transaction.atomic():
                    compra = form.save()
                    compra.detalles.all().delete()  # Eliminar detalles antiguos
                    
                    # Procesar los items como en crear_compra
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

                            if unidades[i] == 'kg':
                                precio_por_gramo = precio / 1000
                                cantidad_en_gramos = cantidad * 1000
                            else:
                                precio_por_gramo = precio
                                cantidad_en_gramos = cantidad

                            item, _ = Item.objects.get_or_create(
                                nombre=nombre_item,
                                defaults={
                                    'tipo': tipos[i],
                                    'unidad_medida': unidades[i]
                                }
                            )

                            DetalleCompra.objects.create(
                                compra=compra,
                                item=item,
                                cantidad=cantidad_en_gramos,
                                precio_compra=precio_por_gramo
                            )

                        except (InvalidOperation, ValueError) as e:
                            raise ValidationError(f"Error en ítem {i+1}: {str(e)}")
                    
                    compra.calcular_totales()
                    messages.success(request, '✅ Compra actualizada exitosamente!')
                    return redirect('administrador:detalle_compra', compra_id=compra.id)
                    
            except Exception as e:
                messages.error(request, f'❌ Error al actualizar: {str(e)}')
    else:
        form = CompraForm(instance=compra)
        
        # Preparar datos para el template
        detalles = compra.detalles.all().select_related('item')
        items_data = []
        
        for detalle in detalles:
            # Convertir unidades para mostrar (kg → gramos)
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
#ELIMINAR COMPRA
def eliminar_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    compra.delete()
    messages.success(request, f'Compra #{compra.numero_factura} eliminada correctamente')
    return redirect('administrador:lista_compras')

# CATEGORIAS

def categorias(request):
    return render(request, 'categorias/categorias.html')

def crear_categorias(request):
    if request.method == 'POST':
        form = CategoriaProductoForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            html = render_to_string('categorias/partials/categoria_row_partial.html', {'categoria': categoria})
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
            categoria = form.save()
            html = render_to_string('categorias/partials/categoria_row_partial.html', {'categoria': categoria})
            response = HttpResponse(html)
            response['HX-Trigger'] = 'modalCategoriaCerrado'
            return response
        else:
            return render(request, 'categorias/partials/categoria_form_partial.html', {'form': form})
    else:
        form = CategoriaProductoForm(instance=categoria)
        return render(request, 'categorias/partials/categoria_form_partial.html', {'form': form})
