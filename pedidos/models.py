from django.db import models

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

    cliente = models.ForeignKey('administrador.Cliente', on_delete=models.CASCADE, related_name='pedidos')
    # CODIGO PEDIENTE PARA REVISION
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField()
    estado = models.CharField(max_length=20, default='Pediente') # PEDIENTE PARA REVISION
    direccion_entrega = models.CharField(max_length=255, blank=True, null=True) # PEDIENTE PARA REVISION
    tipo_entrega = models.CharField(max_length=2, choices=TIPO_ENTREGA_CHOICES, default='RE')
    hora_retiro = models.TimeField(null=True, blank=True)

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