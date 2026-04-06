from django.contrib import admin
from .models import Ciudad, Barrio, Persona, Cliente, Empleado, Proveedor, Salario, TipoEmpleado, Direccion, Producto, CategoriaProducto, IngredienteProducto, Mesa

admin.site.register([Ciudad, Barrio, Persona, Cliente, Empleado, Proveedor, Salario, TipoEmpleado, Direccion, Producto, CategoriaProducto, IngredienteProducto, Mesa])

