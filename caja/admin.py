from django.contrib import admin

from .models import Caja, Cuenta, VentaCaja, MovimientoCaja
# Register your models here.


admin.site.register(Caja)
admin.site.register(Cuenta)
admin.site.register(VentaCaja)
admin.site.register(MovimientoCaja)