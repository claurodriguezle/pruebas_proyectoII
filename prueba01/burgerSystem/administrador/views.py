from django.shortcuts import render, redirect, get_object_or_404
from .models import Persona, Cliente, Empleado, Proveedor, Producto
from .forms import PersonaForm, ProductoForm
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.db import connection, transaction

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