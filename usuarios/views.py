from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from administrador.models import Cliente, Empleado
from usuarios.forms import RegistroClienteForm
from django.contrib import messages
from django.db import transaction

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

                    # Crear el cliente
                    cliente = form.save(commit=False)
                    cliente.user = user
                    cliente.ruc = form.cleaned_data.get('ruc')
                    cliente.save()
                    
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
            return redirect('pedidos:menu_productos')
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

@login_required
def exit(request):
    logout(request)
    return redirect('pedidos:menu_productos')

