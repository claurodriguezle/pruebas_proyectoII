from django.shortcuts import render

def index(request):
    return render(request, 'pedidos/index.html')

def menu_productos(request):
    return render(request, 'pedidos/menu_productos.html')