from django.db import models

# Create your models here.
from django.db import models
from django.utils.timezone import now
from decimal import Decimal
from django.utils import timezone

# Create your models here.
class Timbrado(models.Model):
    numero = models.CharField("Numero de timbrado", max_length=20, unique= True)
    ruc = models.CharField("Ruc del emisor", max_length=20)
    fecha_inicio_vigencia = models.DateField("Inicio de vigencia")
    fecha_fin_vigencia = models.DateField("Fin de Vigencia")
    activo = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)  # Nuevo campo
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)  # Nuevo campo

    def soft_delete(self):
        """Marca el timbrado como eliminado sin borrarlo de la BD"""
        self.eliminado = True
        self.fecha_eliminacion = timezone.now()
        self.save()

    def restore(self):
        """Restaura un timbrado eliminado"""
        self.eliminado = False
        self.fecha_eliminacion = None
        self.save()

    def __str__(self):
        return f"Timbrado {self.numero} - {self.ruc}"

    def clean(self):
        if self.activo:
            #Si se activa este timbrado, desactiva todos los demas
            Timbrado.objects.exclude(id=self.id).update(activo=False)

class Factura(models.Model):
    cod_fact = models.AutoField(primary_key=True)
    nro_fact = models.CharField(max_length=20, unique=True)  # Ej: 001-001-0000162
    cliente = models.ForeignKey('administrador.Cliente', on_delete=models.PROTECT, related_name='facturas')

    # Datos legales
    timbrado = models.ForeignKey(
        Timbrado, 
        on_delete=models.PROTECT,
        limit_choices_to={'activo': True, 'eliminado': False}
    )

    # Datos del cliente para la factura (puede facturar a otro nombre)
    nombre_cliente = models.CharField(max_length=100)
    direccion_cliente = models.CharField(max_length=200)
    telefono_cliente = models.CharField(max_length=20)
    ruc_cliente = models.CharField(max_length=20)

    # Montos
    subtotal = models.BigIntegerField(default=0)
    iva_10 = models.BigIntegerField(default=0)
    total_iva = models.BigIntegerField(default=0)
    monto_total = models.BigIntegerField(default=0)
    descuento = models.BigIntegerField(default=0)

    forma_de_pago = models.CharField(max_length=20, choices=[('EFECTIVO', 'Efectivo')], default='EFECTIVO')
    fecha_emision = models.DateField(default=now)

    def __str__(self):
        return f"Factura {self.nro_fact}"

    def calcular_totales(self):
        total_bruto = 0
        iva_10 = 0

        for detalle in self.detalles.all():
            total_item = detalle.precio_unitario * detalle.cantidad
            precio_sin_iva = total_item / Decimal('1.10')
            iva_item = total_item - precio_sin_iva

            total_bruto += precio_sin_iva
            iva_10 += iva_item

        self.subtotal = round(total_bruto)
        self.iva_10 = round(iva_10)
        self.total_iva = self.iva_10
        self.monto_total = round(total_bruto + iva_10 - self.descuento)
        self.save()

class DetalleFactura(models.Model):
    cod_det_fact = models.AutoField(primary_key=True)
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('administrador.Producto', on_delete=models.PROTECT)
    
    descripcion = models.CharField(max_length=255)
    codigo_producto = models.CharField(max_length=20)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.PositiveIntegerField()
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.descripcion} x {self.cantidad}"
