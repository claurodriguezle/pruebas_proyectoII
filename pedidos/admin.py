from django.contrib import admin

from .models import Pedido
from .models import Adicional
from .models import IngredienteEliminadoPedido

admin.site.register(Pedido)
admin.site.register(Adicional)
admin.site.register(IngredienteEliminadoPedido)