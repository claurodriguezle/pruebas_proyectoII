from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from administrador.models import Cliente, Empleado, Direccion, Ciudad, Barrio
from usuarios.forms import RegistroClienteForm, DireccionForm
from django.contrib import messages
from django.db import transaction, IntegrityError

# Create your views here.
def index(request):
    return render(request, 'usuarios/index.html')

def sesion(request):
    return render(request, 'usuarios/sesion.html')

def registro_cliente(request):
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Crear el usuario
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password1']
                    )

                    # Crear persona
                    persona = form.save()

                    # Crear el cliente asociado a la persona
                    Cliente.objects.create(
                        persona=persona,
                        user=user
                    )
                    
                    messages.success(request, 'Registro exitoso. Ya puedes iniciar sesión.')
                    return redirect('usuarios:sesion')

            except Exception as e:
                messages.error(request, f'Ocurrió un error: {str(e)}')
        else:
            messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = RegistroClienteForm()

    return render(request, 'usuarios/registro_cliente.html', {'form': form})

def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('txtUsuario')
        password = request.POST.get('txtContrasena')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso.')
            #return redirect('pedidos:tipo_entrega')
            #return redirect('pedidos:menu_productos')

            #Redirigir segun el grupo
            if user.is_superuser or user.groups.filter(name='Administrador').exists():
                return redirect('administrador:menu')
            elif user.groups.filter(name='Empleado').exists():
                return redirect('caja:apertura_caja')
            elif user.groups.filter(name='Cocina').exists():
                return redirect('pedidos:cocina')
            else:
                return redirect('pedidos:index')  # clientes
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'usuarios/sesion.html')

@login_required
def perfil_user(request):
    usuario_logueado = request.user

    # Busca si el usuario es un Cliente
    try:
        datos_completos = usuario_logueado.cliente
        tipo = 'Cliente'
    except Cliente.DoesNotExist:
        # Si no es cliente, probamos si es Empleado
        try:
            datos_completos = usuario_logueado.empleado
            tipo = 'Empleado'
        except Empleado.DoesNotExist:
            datos_completos = None
            tipo = 'Usuario sin perfil asociado'
    return render(request, 'usuarios/perfil.html', {
        'perfil': datos_completos,
        'tipo': tipo
    })

# Editar datos guardados del cliente
@login_required
def editar_perfil_cliente(request):
    usuario = request.user
    try:
        perfil = usuario.cliente
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró un perfil asociado.")
        return redirect('usuarios:perfil_user')

    persona = perfil.persona

    if request.method == 'POST':
        nuevo_correo = request.POST.get('correo', usuario.email)
        nombre       = request.POST.get('nombre', persona.nombre)
        apellido     = request.POST.get('apellido', persona.apellido)
        telefono     = request.POST.get('telefono', persona.telefono)
        ruc          = request.POST.get('ruc') or None
        ciudad_id    = request.POST.get('ciudad')
        barrio_id    = request.POST.get('barrio')

        # Validar correo duplicado ANTES de asignarlo
        if User.objects.filter(email=nuevo_correo).exclude(pk=usuario.pk).exists():
            messages.error(request, "El correo ya se encuentra en uso.")
            ciudades = Ciudad.objects.all().order_by('nombre')
            barrios  = Barrio.objects.all().order_by('nombre')
            return render(request, 'usuarios/editar_perfil.html', {
                'perfil'  : perfil,
                'usuario' : usuario,
                'ciudades': ciudades,
                'barrios' : barrios,
            })

        # Asignar valores solo si pasó la validación
        usuario.email    = nuevo_correo
        persona.nombre   = nombre
        persona.apellido = apellido
        persona.telefono = telefono
        persona.ruc      = ruc

        if ciudad_id:
            persona.ciudad_id = ciudad_id
        if barrio_id:
            persona.barrio_id = barrio_id

        try:
            usuario.save()
            persona.save()
            messages.success(request, "Datos actualizados correctamente.")
            return redirect('usuarios:perfil_user')
        except IntegrityError as e:
            if 'ruc' in str(e).lower():
                messages.error(request, "El RUC ya se encuentra en uso.")
            else:
                messages.error(request, "Error al guardar: datos inválidos.")

    ciudades = Ciudad.objects.all().order_by('nombre')
    barrios  = Barrio.objects.all().order_by('nombre')

    return render(request, 'usuarios/editar_perfil.html', {
        'perfil'  : perfil,
        'usuario' : usuario,
        'ciudades': ciudades,
        'barrios' : barrios,
    })

@login_required
def eliminar_cuenta(request):
    if request.method == 'POST':
        usuario = User.objects.get(pk=request.user.pk)

        # Desactiva usuario y persona
        usuario.is_active = False 
        usuario.save()

        try:
            usuario.cliente.persona.estado = False
            usuario.cliente.persona.save()
        except Cliente.DoesNotExist:
            pass

        logout(request)
        messages.success(request, "Tu cuenta ha sido eliminada.")
        return redirect('usuarios:sesion')
    return redirect('usuario:perfil_user')

@login_required
def agregar_direccion(request):
    cliente = request.user.cliente

    if request.method == "POST":
        form = DireccionForm(request.POST)
        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.cliente = cliente

            # Valida la direccion
            if not direccion.latitud or not direccion.longitud:
                messages.error(
                    request,
                    "Debes usar el botón de ubicación antes de guardar la dirección."
                )
                return render(
                    request,
                    "direcciones/agregar.html",
                    {"form": form}
                )

            if direccion.es_principal:
                Direccion.objects.filter(cliente=cliente).update(es_principal=False)
            
            direccion.save()
            return redirect("usuarios:listar_direc")
    
    else:
        form = DireccionForm()
    
    return render(request, "direcciones/agregar.html", {"form": form})

@login_required
def listar_direcciones(request):
    cliente = request.user.cliente
    direcciones = cliente.direcciones.all()

    return render(request, "direcciones/listar_direc.html", {
        "cliente": cliente,
        "direcciones": direcciones
    })

@login_required
def editar_direccion(request, pk):
    cliente = request.user.cliente
    direccion = get_object_or_404(Direccion, pk=pk, cliente=cliente)

    if request.method == 'POST':
        form = DireccionForm(request.POST, instance=direccion)
    
        if form.is_valid():
            direccion = form.save(commit=False)  # Toma los datos nuevos del form

            if not direccion.latitud or not direccion.longitud:
                messages.error(request, "Debes usar el botón de ubicación antes de guardar.")
                return render(request, 'direcciones/agregar.html', {'form': form, 'editando': True})

            if direccion.es_principal:
                Direccion.objects.filter(cliente=cliente).exclude(pk=pk).update(es_principal=False)

            direccion.save()
            messages.success(request, 'Dirección actualizada correctamente.')
            return redirect("usuarios:listar_direc")

    else:
        form = DireccionForm(instance=direccion)

    return render(request, "direcciones/agregar.html", {
        'form': form,
        'editando': True
    })

@login_required
def eliminar_direccion(request, pk):
    cliente = request.user.cliente
    direccion = get_object_or_404(Direccion, pk=pk, cliente=cliente)

    if request.method == 'POST':
        direccion.delete()
        messages.success(request, "Dirección eliminada.")
    
    return redirect("usuarios:listar_direc")

@login_required
def exit(request):
    logout(request)
    #return redirect('pedidos:menu_productos')
    return redirect('usuarios:sesion')