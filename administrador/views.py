from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from decimal import Decimal, InvalidOperation
from .models import Persona, Cliente, Empleado, Proveedor
from .forms import PersonaForm
#Importaciones para Compras
from .models import Compra, DetalleCompra, Item
from .forms import CompraForm
from . import models

# Create your views here.

def menu(request):
    return render(request, 'administrador/menu.html')

def listar_personas(request):
    personas = Persona.objects.all()
    return render(request, 'administrador/listar.html', {
        'personas': personas
    })

def crear_persona(request):
    if request.method == 'POST':
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

            if tipo_persona == 'cliente':
                cliente = Cliente.objects.create(
                    **persona_data,
                    ruc=form.cleaned_data['ruc']
                )
                cliente.save()
            elif tipo_persona == 'empleado':
                empleado = Empleado.objects.create(
                    **persona_data,
                    sueldo=form.cleaned_data['sueldo'],
                    fecha_contratacion=form.cleaned_data['fecha_contratacion'],
                    t_empleado=form.cleaned_data['t_empleado']
                )
                empleado.save()
            elif tipo_persona == 'proveedor':
                proveedor = Proveedor.objects.create(
                    **persona_data,
                    nombre_empresa=form.cleaned_data['nombre_empresa'],
                    ruc=form.cleaned_data['ruc']
                )
                proveedor.save()
            return redirect('listar_personas') # Redirigir a la lista de presonas
    else:
        form = PersonaForm()
    return render(request, 'administrador/registro.html', {'form': form})

def editar_persona(request, id):
    persona = get_object_or_404(Persona, id=id)

    # Determinar el tipo de persona
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
        tipo_persona = None
        instancia_especifica = None

    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona)
        if form.is_valid():
            # Guardar los datos generales de Persona
            persona = form.save()

            # Actualizar los campos específicos según el tipo de persona
            if tipo_persona == 'cliente':
                instancia_especifica.ruc = form.cleaned_data['ruc']
                instancia_especifica.save()
            elif tipo_persona == 'empleado':
                instancia_especifica.sueldo = form.cleaned_data['sueldo']
                instancia_especifica.fecha_contratacion = form.cleaned_data['fecha_contratacion']
                instancia_especifica.t_empleado = form.cleaned_data['t_empleado']
                instancia_especifica.save()
            elif tipo_persona == 'proveedor':
                instancia_especifica.nombre_empresa = form.cleaned_data['nombre_empresa']
                instancia_especifica.ruc = form.cleaned_data['ruc']
                instancia_especifica.save()

            return redirect('listar_personas')
    else:
        # Pasar los valores adicionales como valores iniciales del formulario
        initial_data = {'tipo_persona': tipo_persona}
        if tipo_persona == 'cliente':
            initial_data['ruc'] = instancia_especifica.ruc
        elif tipo_persona == 'empleado':
            initial_data['sueldo'] = instancia_especifica.sueldo
            initial_data['fecha_contratacion'] = instancia_especifica.fecha_contratacion
            initial_data['t_empleado'] = instancia_especifica.t_empleado
        elif tipo_persona == 'proveedor':
            initial_data['nombre_empresa'] = instancia_especifica.nombre_empresa
            initial_data['ruc'] = instancia_especifica.ruc

        form = PersonaForm(instance=persona, initial=initial_data)

    return render(request, 'administrador/registro.html', {'form': form, 'persona': persona})

def eliminar_persona(request, id):
    persona = get_object_or_404(Persona, id=id)
    persona.delete()
    return redirect('listar_personas')

#COMPRAS

def lista_compras(request):
    query = request.GET.get('q', '')
    
    if query:
        compras = Compra.objects.filter(
            models.Q(numero_factura__icontains=query) |
            models.Q(proveedor__nombre_empresa__icontains=query)
        ).select_related('proveedor').order_by('-fecha')
    else:
        compras = Compra.objects.all().select_related('proveedor').order_by('-fecha')
    
    return render(request, 'compras/lista_compras.html', {'compras': compras, 'query': query})

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
                    return redirect('lista_compras')

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