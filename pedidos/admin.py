from django.contrib import admin

from .models import Pedido
from .models import Adicional
from .models import IngredienteEliminadoPedido
from .models import DetallePedido
from .models import DetalleAdicionalPedido

admin.site.register(Pedido)
admin.site.register(Adicional)
admin.site.register(IngredienteEliminadoPedido)
admin.site.register(DetallePedido)
admin.site.register(DetalleAdicionalPedido)