from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from administrador.models import Persona, Cliente, Empleado,TipoEmpleado, Direccion, Ciudad, Barrio
from usuarios.forms import RegistroClienteForm, DireccionForm, UsuarioAdminForm, CambiarPasswordAdminForm
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.http import HttpResponse
from django.contrib.auth.models import Group, Permission

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

'''def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('txtUsuario')
        password = request.POST.get('txtContrasena')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso.')
            return redirect('pedidos:tipo_entrega')
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
    
    return render(request, 'usuarios/sesion.html')'''
def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('txtUsuario')
        password = request.POST.get('txtContrasena')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # 🔒 VERIFICAR que NO sea empleado
            grupos_empleados = ['Administrador', 'Empleado', 'Cocina']
            es_empleado = user.groups.filter(name__in=grupos_empleados).exists() or user.is_superuser
            
            if es_empleado:
                messages.error(request, '⚠️ Este portal es solo para clientes. Los empleados deben usar su portal exclusivo.')
                return render(request, 'usuarios/sesion.html')
            
            # Si llega aquí, es un cliente normal
            login(request, user)
            messages.success(request, 'Inicio de sesión exitoso.')
            return redirect('pedidos:index')  # Clientes van al menú de pedidos
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


#Vistas para administrar los usuarios
def _get_perfil(user):
    """Devuelve (tipo, objeto_perfil, persona) para un User dado."""
    try:
        emp = user.empleado
        return 'Empleado', emp, emp.persona
    except Empleado.DoesNotExist:
        pass
    try:
        cli = user.cliente
        return 'Cliente', cli, cli.persona
    except Cliente.DoesNotExist:
        pass
    return 'Sin perfil', None, None
 
 
@login_required
def index(request):
    """Lista todos los usuarios con filtros por grupo y búsqueda."""
    usuarios = User.objects.select_related(
        'empleado__persona',
        'cliente__persona',
    ).prefetch_related('groups').order_by('username')
 
    # Filtro por grupo
    grupo_filtro = request.GET.get('grupo', '')
    if grupo_filtro == 'sin_rol':
        usuarios = [u for u in usuarios if not u.groups.exists()]
    elif grupo_filtro:
        usuarios = usuarios.filter(groups__name=grupo_filtro)
 
    # Búsqueda por nombre o cédula
    search = request.GET.get('search', '').strip()
    if search:
        usuarios_filtrados = []
        for u in usuarios:
            _, _, persona = _get_perfil(u)
            if persona:
                if (search.lower() in persona.nombre.lower() or
                        search.lower() in persona.apellido.lower() or
                        search in persona.cedula):
                    usuarios_filtrados.append(u)
            else:
                if search.lower() in u.username.lower():
                    usuarios_filtrados.append(u)
        usuarios = usuarios_filtrados
 
    # Armar lista con datos ya procesados para el template
    tabla = []
    for u in usuarios:
        tipo, perfil, persona = _get_perfil(u)
        grupo = u.groups.first()
        tabla.append({
            'user': u,
            'persona': persona,
            'tipo': tipo,
            'grupo': grupo.name if grupo else 'Cliente',
        })
 
    grupos = Group.objects.all()
 
    return render(request, 'usuarios/index.html', {
        'tabla': tabla,
        'grupos': grupos,
        'grupo_filtro': grupo_filtro,
        'search': search,
    })
 
 
@login_required
def crear_usuario_admin(request):
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=cd['username'],
                        email=cd['email'],
                        password=cd['password1'],
                    )
                    grupo = cd.get('grupo')
                    if grupo:
                        user.groups.set([grupo])
                    user.save()
 
                    persona = Persona.objects.create(
                        nombre=cd['nombre'],
                        apellido=cd['apellido'],
                        cedula=cd['cedula'],
                        telefono=cd['telefono'],
                        fecha_nacimiento=cd['fecha_nacimiento'],
                        nacionalidad=cd['nacionalidad'],
                        ruc=cd.get('ruc') or None,
                        correo=cd['email'],
                        ciudad=cd['ciudad'],
                        barrio=cd['barrio'],
                    )

                    GRUPOS_EMPLEADO = ['Administrador', 'Cocina', 'Empleado']
 
                    if grupo and grupo.name in GRUPOS_EMPLEADO:
                        Empleado.objects.create(
                            persona=persona,
                            user=user,
                            tipo=cd.get('tipo_empleado'),
                            fecha_contratacion=cd['fecha_contratacion'],
                            salario=cd.get('salario'),       # ← CAMPO NUEVO
                        )
                    else:
                        Cliente.objects.create(persona=persona, user=user)
 
                messages.success(request, f'Usuario "{user.username}" creado correctamente.')
                return HttpResponse(status=204, headers={'HX-Trigger': 'usuarioGuardado'})
 
            except Exception as e:
                messages.error(request, f'Error al crear el usuario: {str(e)}')
 
        return render(request, 'usuarios/partials/modal_form.html', {
            'form': form, 'modo': 'crear'
        })
 
    form = UsuarioAdminForm()
    return render(request, 'usuarios/partials/modal_form.html', {
        'form': form, 'modo': 'crear'
    })
 
 
@login_required
def editar_usuario_admin(request, pk):
    user = get_object_or_404(User, pk=pk)
    tipo, perfil, persona = _get_perfil(user)
 
    initial = {
        'username': user.username,
        'email': user.email,
        'grupo': user.groups.first(),
        'nombre': persona.nombre if persona else '',
        'apellido': persona.apellido if persona else '',
        'cedula': persona.cedula if persona else '',
        'telefono': persona.telefono if persona else '',
        'fecha_nacimiento': persona.fecha_nacimiento.strftime('%Y-%m-%d') if persona and persona.fecha_nacimiento else '',
        'nacionalidad': persona.nacionalidad if persona else '',
        'ruc': persona.ruc if persona else '',
        'ciudad': persona.ciudad if persona else None,
        'barrio': persona.barrio if persona else None,
    }
 
    if tipo in ['Administrador', 'Cocina', 'Empleado'] and perfil:
        initial['tipo_empleado'] = perfil.tipo
        initial['fecha_contratacion'] = perfil.fecha_contratacion.strftime('%Y-%m-%d') if perfil.fecha_contratacion else ''
        initial['salario'] = perfil.salario
 
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, usuario_id=pk)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    user.username = cd['username']
                    user.email = cd['email']
                    if cd.get('password1'):
                        user.set_password(cd['password1'])
                    user.save()
 
                    grupo = cd.get('grupo')
                    user.groups.clear()
                    if grupo:
                        user.groups.add(grupo)
 
                    if not persona:
                        persona = Persona.objects.create(
                            nombre=cd['nombre'],
                            apellido=cd['apellido'],
                            cedula=cd['cedula'],
                            telefono=cd['telefono'],
                            fecha_nacimiento=cd['fecha_nacimiento'],
                            nacionalidad=cd['nacionalidad'],
                            ruc=cd.get('ruc') or None,
                            correo=cd['email'],
                            ciudad=cd['ciudad'],
                            barrio=cd['barrio'],
                        )
                        #Crear o actualizar perfil según el grupo
                        grupo = cd.get('grupo')
                        if grupo and grupo.name in ['Administrador', 'Cocina', 'Empleado']:
                            Empleado.objects.create(
                                persona=persona,
                                user=user,
                                tipo=cd.get('tipo_empleado'),
                                fecha_contratacion=cd.get('fecha_contratacion'),
                                salario=cd.get('salario'),
                            )
                        else:
                            Cliente.objects.create(persona=persona, user=user)
                    else:
                        persona.nombre = cd['nombre']
                        persona.apellido = cd['apellido']
                        persona.cedula = cd['cedula']
                        persona.telefono = cd['telefono']
                        persona.fecha_nacimiento = cd['fecha_nacimiento']
                        persona.nacionalidad = cd['nacionalidad']
                        persona.ruc = cd.get('ruc') or None
                        persona.correo = cd['email']
                        persona.ciudad = cd['ciudad']
                        persona.barrio = cd['barrio']
                        persona.save()

                        if tipo in ['Administrador', 'Cocina', 'Empleado'] and perfil:
                            perfil.tipo = cd.get('tipo_empleado')
                            perfil.fecha_contratacion = cd.get('fecha_contratacion')
                            perfil.salario = cd.get('salario')
                            perfil.save()
    
                messages.success(request, f'Usuario "{user.username}" actualizado.')
                return HttpResponse(status=204, headers={'HX-Trigger': 'usuarioGuardado'})
 
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
 
        return render(request, 'usuarios/partials/modal_form.html', {
            'form': form, 'modo': 'editar', 'usuario': user
        })
 
    form = UsuarioAdminForm(initial=initial, usuario_id=pk)
    return render(request, 'usuarios/partials/modal_form.html', {
        'form': form, 'modo': 'editar', 'usuario': user
    })
 
@login_required
def toggle_activo(request, pk):
    """Activa o desactiva un usuario (no elimina)."""
    if request.method == 'POST':
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
 
        # También actualizar estado de la Persona
        _, _, persona = _get_perfil(user)
        if persona:
            persona.estado = user.is_active
            persona.save()
 
        estado = 'activado' if user.is_active else 'desactivado'
        messages.success(request, f'Usuario "{user.username}" {estado}.')
 
    return redirect('usuarios:index')
 
 
@login_required
def cambiar_password_admin(request, pk):
    """El admin cambia la contraseña de cualquier usuario."""
    user = get_object_or_404(User, pk=pk)
 
    if request.method == 'POST':
        form = CambiarPasswordAdminForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, f'Contraseña de "{user.username}" actualizada.')
            return HttpResponse(status=204, headers={'HX-Trigger': 'usuarioGuardado'})
        return render(request, 'usuarios/partials/modal_password.html', {
            'form': form, 'usuario': user
        })
 
    form = CambiarPasswordAdminForm()
    return render(request, 'usuarios/partials/modal_password.html', {
        'form': form, 'usuario': user
    })

# ==================== NUEVAS VISTAS PARA EMPLEADOS ====================

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.shortcuts import redirect
from administrador.models import Empleado
from django.db import transaction

def login_empleado(request):
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard_redireccion')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            grupos_empleados = ['Administrador', 'Empleado', 'Cocina']
            user_groups = list(user.groups.values_list('name', flat=True))
            
            if any(grupo in grupos_empleados for grupo in user_groups):
                login(request, user)
                messages.success(request, f'Bienvenido {user.get_full_name() or user.username}')
                return redirect('usuarios:dashboard_redireccion')
            else:
                messages.error(request, 'No tienes permisos de empleado. Usa el portal de clientes.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'usuarios/login.html')

def logout_empleado(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('usuarios:login_empleado')

@login_required
def perfil_empleado(request):
    usuario = request.user
    
    try:
        empleado = usuario.empleado
        persona = empleado.persona
    except Empleado.DoesNotExist:
        messages.error(request, 'No se encontró información de empleado asociada.')
        return redirect('usuarios:dashboard_redireccion')
    
    # Construir dirección completa
    direccion = f"{persona.barrio.nombre if persona.barrio else ''}, {persona.ciudad.nombre if persona.ciudad else ''}"
    
    # Verificar si es administrador
    es_admin = request.user.groups.filter(name='Administrador').exists()
    
    contexto = {
        'usuario': usuario,
        'persona': persona,
        'empleado': empleado,
        'direccion': direccion,
        'rol': request.user.groups.first().name if request.user.groups.first() else 'Empleado',
        'es_admin': es_admin,
    }
    
    return render(request, 'usuarios/perfil_empleado.html', contexto)

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Administrador').exists())
def editar_perfil_empleado(request, pk):
    from django.contrib.auth.models import User
    usuario = get_object_or_404(User, pk=pk)
    
    try:
        empleado = usuario.empleado
        persona = empleado.persona
    except Empleado.DoesNotExist:
        messages.error(request, 'El usuario no es un empleado.')
        return redirect('usuarios:index')
    
    if request.method == 'POST':
        with transaction.atomic():
            usuario.email = request.POST.get('email', usuario.email)
            usuario.save()
            
            persona.nombre = request.POST.get('nombre', persona.nombre)
            persona.apellido = request.POST.get('apellido', persona.apellido)
            persona.telefono = request.POST.get('telefono', persona.telefono)
            persona.fecha_nacimiento = request.POST.get('fecha_nacimiento', persona.fecha_nacimiento)
            persona.nacionalidad = request.POST.get('nacionalidad', persona.nacionalidad)
            
            persona.save()
        
        messages.success(request, f'Perfil de {persona.nombre} {persona.apellido} actualizado correctamente.')
        return redirect('usuarios:perfil_empleado')
    
    return redirect('usuarios:perfil_empleado')

@login_required
def dashboard_redireccion(request):
    grupo = request.user.groups.first()
    
    if not grupo:
        return redirect('pedidos:index')
    
    if grupo.name == 'Administrador':
        return redirect('administrador:menu')
    elif grupo.name == 'Empleado':
        return redirect('caja:apertura_caja')
    elif grupo.name == 'Cocina':
        return redirect('pedidos:cocina')
    else:
        return redirect('pedidos:index')

#Vistas para administrar los grupos y permisos
@login_required
def lista_grupos(request):
    grupos = Group.objects.prefetch_related('user_set').order_by('name')
    return render(request, 'usuarios/grupos/lista.html', {'grupos': grupos})


@login_required
def crear_grupo(request):
    permisos = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'name'
    )
    if request.method == 'POST':
        nombre = request.POST.get('name', '').strip()
        permisos_ids = request.POST.getlist('permissions')

        if not nombre:
            messages.error(request, 'El nombre del grupo es obligatorio.')
        elif Group.objects.filter(name__iexact=nombre).exists():
            messages.error(request, f'Ya existe un grupo llamado "{nombre}".')
        else:
            grupo = Group.objects.create(name=nombre)
            if permisos_ids:
                grupo.permissions.set(permisos_ids)
            messages.success(request, f'Grupo "{nombre}" creado correctamente.')
            return redirect('usuarios:lista_grupos')

    return render(request, 'usuarios/grupos/form.html', {
        'permisos': permisos,
        'grupo': None,
        'permisos_elegidos': [],
        'modo': 'crear'
    })


@login_required
def editar_grupo(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    permisos = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'name'
    )
    permisos_elegidos = list(grupo.permissions.values_list('id', flat=True))

    if request.method == 'POST':
        nombre = request.POST.get('name', '').strip()
        permisos_ids = request.POST.getlist('permissions')

        if not nombre:
            messages.error(request, 'El nombre del grupo es obligatorio.')
        elif Group.objects.filter(name__iexact=nombre).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe un grupo llamado "{nombre}".')
        else:
            grupo.name = nombre
            grupo.permissions.set(permisos_ids)
            grupo.save()
            messages.success(request, f'Grupo "{nombre}" actualizado correctamente.')
            return redirect('usuarios:lista_grupos')

    return render(request, 'usuarios/grupos/form.html', {
        'permisos': permisos,
        'grupo': grupo,
        'permisos_elegidos': permisos_elegidos,
        'modo': 'editar'
    })


@login_required
def eliminar_grupo(request, pk):
    grupo = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        usuarios_con_grupo = grupo.user_set.count()
        if usuarios_con_grupo > 0:
            messages.error(request, f'No se puede eliminar: {usuarios_con_grupo} usuario(s) pertenecen a este grupo.')
        else:
            nombre = grupo.name
            grupo.delete()
            messages.success(request, f'Grupo "{nombre}" eliminado.')
    return redirect('usuarios:lista_grupos')