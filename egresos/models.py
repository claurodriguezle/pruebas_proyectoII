from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from caja.models import Caja
from administrador.models import Proveedor, Compra


class Egreso(models.Model):

    CATEGORIA_CHOICES = [
        ('SERVICIOS', 'Servicios'),
        ('SUELDOS', 'Sueldos'),
        ('LIMPIEZA', 'Limpieza'),
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('IMPUESTOS', 'Impuestos'),
        ('COMPRAS', 'Compras'),  
        ('OTRO', 'Otro'),
    ]

    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('ANULADO', 'Anulado'),
    ]

    fecha = models.DateField(verbose_name="Fecha del gasto")
    monto = models.BigIntegerField(
        verbose_name="Monto en Gs.",
        validators=[MinValueValidator(1)]
    )
    descripcion = models.CharField(
        max_length=255,
        verbose_name="Descripción"
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        verbose_name="Categoría"
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Proveedor",
        related_name="egresos"
    )
    compra = models.OneToOneField(
        Compra,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='egreso',
        verbose_name="Compra relacionada"
    )
    numero_comprobante = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Número de comprobante"
    )
    caja = models.ForeignKey(
        Caja,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Caja",
        related_name="egresos"
    )
    salio_de_caja = models.BooleanField(
        default=False,
        verbose_name="¿Salió de la caja?"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Registrado por"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='ACTIVO'
    )
    motivo_anulacion = models.TextField(
        null=True,
        blank=True,
        verbose_name="Motivo de anulación"
    )

    def __str__(self):
        return f"{self.get_categoria_display()} - ₲{self.monto:,} ({self.fecha})"

    class Meta:
        verbose_name = "Egreso"
        verbose_name_plural = "Egresos"
        ordering = ['-fecha', '-fecha_registro']