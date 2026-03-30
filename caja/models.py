from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Caja(models.Model):
    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]

    usuario_apertura = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cajas_apertura'
    )
    usuario_cierre = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cajas_cierre',
        null=True,
        blank=True
    )
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    monto_inicial = models.BigIntegerField(
        default=0,
        help_text="Monto en guaraníes con el que se abre la caja"
    )
    monto_final_esperado = models.BigIntegerField(
        default=0,
        help_text="Calculado: monto_inicial + ventas - egresos"
    )
    monto_final_real = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="El dinero que realmente había al cerrar"
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='abierta'
    )
    observaciones_cierre = models.TextField(blank=True, null=True)

    @property
    def diferencia(self):
        """Sobrante (+) o faltante (-) al cerrar."""
        if self.monto_final_real is not None and self.monto_final_esperado is not None:
            return self.monto_final_real - self.monto_final_esperado
        return None

    @property
    def total_ventas(self):
        return self.ventas.filter(anulado=False).aggregate(
            total=models.Sum('total')
        )['total'] or 0

    @property
    def total_egresos(self):
        return self.movimientos.filter(
            tipo='egreso'
        ).aggregate(total=models.Sum('monto'))['total'] or 0

    def recalcular_monto_esperado(self):
        self.monto_final_esperado = self.monto_inicial + self.total_ventas - self.total_egresos
        self.save(update_fields=['monto_final_esperado'])

    def __str__(self):
        return f"Caja #{self.id} — {self.fecha_apertura.strftime('%d/%m/%Y')} [{self.get_estado_display()}]"

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"
        ordering = ['-fecha_apertura']


class VentaCaja(models.Model):
    """
    Registra cada venta realizada desde el POS.
    Crea un Pedido en la app pedidos y lo vincula acá.
    """
    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        related_name='ventas'
    )
    pedido = models.OneToOneField(
        'pedidos.Pedido',
        on_delete=models.PROTECT,
        related_name='venta_caja',
        null=True,
        blank=True
    )
    cliente = models.ForeignKey(
        'administrador.Cliente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha = models.DateTimeField(default=timezone.now)
    total = models.BigIntegerField(help_text="Total en guaraníes")
    monto_recibido = models.BigIntegerField(help_text="Efectivo recibido")
    vuelto = models.BigIntegerField(default=0)
    tipo_entrega = models.CharField(
        max_length=2,
        choices=[('RE', 'Retiro en local'), ('DE', 'Delivery')],
        default='RE'
    )
    anulado = models.BooleanField(default=False)
    motivo_anulacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Venta #{self.id} — Caja #{self.caja_id} — ₲{self.total:,}"

    class Meta:
        verbose_name = "Venta de Caja"
        verbose_name_plural = "Ventas de Caja"
        ordering = ['-fecha']


class MovimientoCaja(models.Model):
    """
    Egresos manuales (gastos del día) registrados durante el turno.
    Los ingresos son las VentaCaja.
    """
    TIPO_CHOICES = [
        ('egreso', 'Egreso'),
    ]

    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='egreso')
    descripcion = models.CharField(max_length=200)
    monto = models.BigIntegerField(help_text="Monto en guaraníes")
    fecha = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.get_tipo_display()} ₲{self.monto:,} — {self.descripcion}"

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ['-fecha']