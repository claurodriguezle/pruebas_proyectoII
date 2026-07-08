from django.contrib import admin

from .models import Factura
from .models import DetalleFactura

admin.site.register(Factura)
admin.site.register(DetalleFactura)

