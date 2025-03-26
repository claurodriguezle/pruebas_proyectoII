from django.shortcuts import render, redirect, get_object_or_404
from .models import Persona, Cliente, Empleado, Proveedor
from .forms import PersonaForm
from django.db import IntegrityError

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

                return redirect('listar_personas')

            except IntegrityError as e:
                # Maneja errores de unicidad
                form.add_error(None, "Error al guardar. Verifica los datos únicos.")
                print(f"Error de integridad: {e}")

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
