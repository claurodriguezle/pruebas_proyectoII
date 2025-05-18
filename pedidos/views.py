from django.shortcuts import render
from administrador.models import Producto, CategoriaProducto

def index(request):
    return render(request, 'pedidos/index.html')

def menu_productos(request):
    categorias = CategoriaProducto.objects.all()
    return render(request, 'pedidos/menu_productos.html', {'categorias': categorias})

def lista_productos(request):
    categoria_nombre = request.GET.get('categoria')
    if categoria_nombre:
        productos = Producto.objects.filter(estado='A', categoria__nombre_categ=categoria_nombre)
    else:
        productos = Producto.objects.filter(estado='A')
    return render(request, 'pedidos/partials/productos_lista.html', {'productos': productos})