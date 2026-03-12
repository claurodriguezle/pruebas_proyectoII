from django.db import models
from django.core.exceptions import ValidationError

class Adicional(models.Model):
    nombre = models.CharField(max_length=50)
    precio = models.IntegerField()

    def __str__(self):
        return f"{self.nombre} (₲{self.precio})"
    

class Pedido(models.Model):
    TIPO_ENTREGA_CHOICES = [
        ('RE', 'Retiro en local'),
        ('DE', 'Delivery'),
    ]

    ESTADO_CHOICES = [
        ('PE', 'Pendiente'),
        ('EC', 'En camino'),
        ('EN', 'Entregado'),
        ('CA', 'Cancelado'),
    ]

    cliente = models.ForeignKey('administrador.Cliente', on_delete=models.CASCADE, related_name='pedidos')
    # CODIGO PEDIENTE PARA REVISION
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField()
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='PE')
    tipo_entrega = models.CharField(max_length=2, choices=TIPO_ENTREGA_CHOICES, default='RE')
    direccion_entrega = models.ForeignKey(
        'administrador.Direccion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pedidos'
    )

    costo_delivery = models.IntegerField(
        null=True,
        blank=True,
        default=0
    )

    # Guarda la direccion para el historial
    direccion_snapshot = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    hora_retiro = models.TimeField(null=True, blank=True)

    def clean(self):
        if self.tipo_entrega == 'DE' and not self.direccion_entrega:
            raise ValidationError("Debe seleccionar una dirección para delivery.")
        
        if self.tipo_entrega == 'RE':
            self.direccion_entrega = None
            self.direccion_snapshot = None
    
    def save(self, *args, **kwargs):
        if self.tipo_entrega == 'DE' and self.direccion_entrega:
            direccion = self.direccion_entrega

            self.direccion_snapshot = (
                f"{direccion.nombre} - {direccion.direccion_text}, "
                f"{direccion.barrio.nombre}, "
                f"{direccion.barrio.ciudad.nombre}"
            )

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.get_tipo_entrega_display()}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalle')
    producto = models.ForeignKey('administrador.Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.IntegerField()
    nota = models.TextField(max_length=200, blank=True, null=True)

    def subtotal(self):
        # Precio base x cantidad + suma adicionales
        return self.precio_unitario * self.cantidad
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

class DetalleAdicionalPedido(models.Model):
    detalle_pedido = models.ForeignKey(DetallePedido, on_delete=models.CASCADE, related_name='adicionales')
    adicional = models.ForeignKey(Adicional, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.adicional.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.adicional.nombre}"

class IngredienteEliminadoPedido(models.Model):
    detalle_pedido = models.ForeignKey(DetallePedido, on_delete=models.CASCADE, related_name='ingredientes_eliminados')
    ingrediente = models.ForeignKey('administrador.IngredienteProducto', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.ingrediente.nombre} en {self.detalle_pedido}"