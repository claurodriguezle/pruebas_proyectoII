from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm

# Create your views here.

def menu(request):
    return render(request, 'administrador/menu.html')

def listar(request):
    clientes = Cliente.objects.all()
    return render(request, 'administrador/listar.html', {
        'clientes': clientes
    })

def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar')
    else:
        form = ClienteForm()
    return render(request, 'administrador/registro.html', {
        'form': form
    })

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'administrador/registro.html',{
        'form': form,
        'cliente': cliente
    })

def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.delete()
    return redirect('listar')