from django.db import models
from django.core.exceptions import ValidationError
from administrador .models import Item

class Adicional(models.Model):
    nombre = models.CharField(max_length=50)
    precio = models.IntegerField()
    item = models.ForeignKey(
        'administrador.Item',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Item de stock'
    )
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='Cantidad en gramos'
    )

    def __str__(self):
        return f"{self.nombre} (₲{self.precio})"
    
class Pedido(models.Model):
    #Tipo de entrega
    TIPO_ENTREGA_CHOICES = [
        ('RE', 'Retiro en local'),
        ('DE', 'Delivery'),
    ]

    #Estado de cocina (lo maneja el Panel de Cocina)
    ESTADO_COCINA_CHOICES = [
        ('PE','Pendiente'),  #recien entro, cocina aun no lo vio
        ('EP','En preparacion'), #cocina lo esta preparando
        ('LI','Listo'),     #cocina termino, listo para entregar
    ]

    ESTADO_ENTREGA_CHOICES = [
        ('PE', 'Pendiente'), #aun no fue entregado al cliente
        ('EN','Entregado'),  #el empleado lo entrego al cliente
        ('FA', 'Facturado'), #se genero y envio la factura
        ('CA','Cancelado'),   #cancelado(cualquier momento)
    ]

    cliente = models.ForeignKey('administrador.Cliente', on_delete=models.CASCADE, related_name='pedidos')
    # CODIGO PEDIENTE PARA REVISION
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField()

    #Estados de los pedidos
    estado_cocina = models.CharField(max_length=2,choices=ESTADO_COCINA_CHOICES, default='PE', verbose_name='Estado de cocina')
    estado_entrega = models.CharField(max_length=2,choices=ESTADO_ENTREGA_CHOICES, default='PE',verbose_name='Estado de entrega')


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
    #Propiedades utiles
    @property
    def listo_para_entregar(self):
        """True cuando cocina terminó y el empleado aún no lo entregó."""
        return self.estado_cocina == 'LI' and self.estado_entrega == 'PE'

    @property
    def puede_facturar(self):
        """True cuando ya fue entregado pero aún no tiene factura."""
        return self.estado_entrega == 'EN'

    @property
    def siguiente_estado_cocina(self):
        """Devuelve el código del siguiente estado de cocina, o None si ya llegó al final."""
        mapa = {'PE': 'EP', 'EP': 'LI'}
        return mapa.get(self.estado_cocina)

    @property
    def siguiente_estado_entrega(self):
        """
        Devuelve el código del siguiente estado de entrega, o None.
        Solo permite avanzar si cocina ya marcó Listo.
        """
        if self.estado_entrega == 'PE' and self.estado_cocina == 'LI':
            return 'EN'
        if self.estado_entrega == 'EN':
            return 'FA'
        return None
    #Validaciones

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
        return f"{self.ingrediente.item.nombre} en {self.detalle_pedido}"