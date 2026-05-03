from django.contrib import admin
from .models import Ciudad, Barrio, Persona, Cliente, Empleado, Proveedor, Salario, TipoEmpleado, Direccion, Producto, CategoriaProducto, IngredienteProducto, Mesa, Stock, Item

admin.site.register([Ciudad, Barrio, Persona, Cliente, Empleado, Proveedor, Salario, TipoEmpleado, Direccion, CategoriaProducto, IngredienteProducto, Mesa, Stock, Item])

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    filter_horizontal = ('adicionales',)

