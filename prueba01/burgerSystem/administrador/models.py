from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    fecha_nacimiento = models.DateField()
    cedula = models.CharField(max_length=15, unique=True)
    ciudad = models.CharField(max_length=100)
    barrio = models.CharField(max_length=100)
    nacionalidad = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Cliente(Persona):
    ruc = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Cliente: {self.nombre} {self.apellido}"

class Empleado(Persona):
    sueldo = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_contratacion = models.DateField()
    t_empleado = models.CharField(max_length=100)

    def __str__(self):
        return f"Empleado:{self.nombre} {self.apellido} "

class Proveedor(Persona):
    nombre_empresa = models.CharField(max_length=150)
    ruc = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Proveedor: {self.nombre_empresa}"

#Modelos para compras
#ITEM
class Item(models.Model):
    #Nos permite distinguir si es un articulo o materia prima para poder aplicar la transformacion de unidades adecuada
    UNIDAD_CHOICES = [
        ('unidad','Unidad'),
        ('kg','Kilogramo'),
        ('gr','Gramo'),
        ('lt','Litro'),
        ('ml','Mililitro'),
    ]
    TIPO_CHOICES = [
        ('MATERIA_PRIMA', 'Materia Prima'),
        ('ARTICULO','Articulo'),
    ]
    nombre = models.CharField(max_length=255, verbose_name="Nombre del item")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES,default='ARTICULO',verbose_name="Tipo de item")
    unidad_medida = models.CharField(max_length=50,choices=UNIDAD_CHOICES, default='unidad')
    def __str__(self):
        return f"{self.nombre}({self.get_unidad_medida_display()})"
    #Metodo que devuelve la unidad de medida segun el tipo de item
    def get_unidad_medida_display(self):
        if self.tipo == 'Materia_PRIMA':
            return 'gramos'
        elif self.tipo == 'ARTICULO':
            return 'unidades'
        return self.unidad_medida or ''

#DETALLES_COMPRA
class DetalleCompra(models.Model):
    compra = models.ForeignKey('Compra', on_delete=models.CASCADE, related_name='detalles')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10,decimal_places=2, verbose_name="Cantidad")
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de compra")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sub total", editable=False)
    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        if self.precio_compra <= 0:
            raise ValidationError("El precio debe ser mayor a cero")

    #Modulo para calcular automaticamente el subtotal
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_compra
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.nombre} - {self.cantidad} {self.item.get_unidad_medida_display}"
#COMPRAS
class Compra(models.Model):
    numero_factura = models.CharField(
        max_length= 50,
        unique= True,  #El numero de factura debe ser unico
        verbose_name="Numero de factura"
    )
    fecha = models.DateField(verbose_name= "Fecha de Compra")
    proveedor = models.ForeignKey(
        Proveedor, #Relacion con el proveedor
        on_delete=models.PROTECT, #Impide eliminar el proveedor si tiene compras
        verbose_name="Proveedor",
        related_name="compras"
    )
    iva_10 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="IVA 10%",
        validators=[MinValueValidator(0)], #El IVA no puede ser negativo
        default=0
    )
    iva_5 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="IVA 5%",
        validators=[MinValueValidator(0)], 
        default=0
    )
    total_sin_iva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total sin IVA",
        validators=[MinValueValidator(0)],  # El total no puede ser negativo
        default=0  # Valor por defecto
    )
    total_iva = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total IVA",
        validators=[MinValueValidator(0)],  # El total IVA no puede ser negativo
        default=0  # Valor por defecto
    )
    monto_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto total",
        validators=[MinValueValidator(0)], #El monto no puede ser negativo
        default=0 #Valor por defecto
    )
    def __str__(self):
        return f"Factura {self.numero_factura} - {self.proveedor.nombre if self.proveedor else 'Proveedor Eliminado'}(self.fecha)"
    def calcular_totales(self):
        """
        Calcula los totales(total sin iva, iva 5, iva 10, total iva, monto total, basados en los detalles de compra asociados)
        """
        detalles = self.detalles.all() #Accede a los detalles de compra relacionado

        #Inicializar totales
        self.total_sin_iva = 0
        self.iva_5= 0
        self.iva_10 = 0

        #Calcular totales basados en los detalles
        for detalle in self.detalles.all():
            self.total_sin_iva += detalle.subtotal
            if detalle.item.tipo == 'MATERIA_PRIMA':
                self.iva_5 += detalle.subtotal * 0.05
            elif detalle.item.tipo == 'ARTICULO':
                self.iva_10 += detalle.subtotal *0.10
        
        #Calcular derivados
        self.total_iva = self.iva_5 + self.iva_10
        self.monto_total = self.total_sin_iva + self.total_iva

        self.save()
    