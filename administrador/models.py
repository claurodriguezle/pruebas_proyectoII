from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField()
    cedula = models.CharField(max_length=15, unique=True)
    ciudad = models.CharField(max_length=100)
    barrio = models.CharField(max_length=100)
    nacionalidad = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Cliente(Persona):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    ruc = models.CharField(
    max_length=20,
    blank=True,
    null=True,
    default=None
    )

    def __str__(self):
        return f"Cliente: {self.nombre} {self.apellido}"

class Empleado(Persona):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    sueldo = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_contratacion = models.DateField()
    t_empleado = models.CharField(max_length=100)

    def __str__(self):
        return f"Empleado:{self.nombre} {self.apellido} "

class Proveedor(Persona):
    nombre_empresa = models.CharField(max_length=150)
    ruc = models.CharField(
    max_length=20, 
    unique=True,
    blank=True,
    null=True,
    default=None
    )

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
        ('MATERIA_PRIMA', 'Materia_Prima'),
        ('ARTICULO','Articulo'),
    ]
    nombre = models.CharField(max_length=255, verbose_name="Nombre del item")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES,default='ARTICULO',verbose_name="Tipo de item")
    unidad_medida = models.CharField(max_length=50,choices=UNIDAD_CHOICES, default='unidad')
    def __str__(self):
        return f"{self.nombre}({self.get_unidad_medida_display()})"
    #Metodo que devuelve la unidad de medida segun el tipo de item
    def get_unidad_medida_display(self):
        if self.tipo == 'MATERIA_PRIMA':
            return 'gramos'
        elif self.tipo == 'ARTICULO':
            return 'unidades'
        return self.unidad_medida or ''

    #Estandarizar el nombre del item ante de guardar
    def clean(self):
        if self.nombre:
            self.nombre = self.estandarizar_nombre(self.nombre)
        super().clean()
    #Aseguramos que el nombre este estandarizado al guardar
    def save(self, *args, **kwargs):
        self.nombre = self.estandarizar_nombre(self.nombre)
        super().save(*args, **kwargs)

    @staticmethod
    def estandarizar_nombre(nombre):
        '''
        Estandariza el formato de los nombres de items:
        1. Primera letra en mayuscula
        2. Elimina espacios extras
        3. Convierte a singular si termina en 's'
        '''
        nombre = nombre.strip()
        if not nombre:
            return nombre
        
        #Capitalizar primera letra y minusculas el resto
        nombre = nombre[0].upper() + nombre[1:].lower()
        #Eliminar espacios multiples
        nombre=' '.join(nombre.split())
        #Conversion basica a singular
        if nombre.endswith('s') and len(nombre) > 3:
            nombre = nombre[:-1]
        return nombre
    
    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ['nombre']

#DETALLES_COMPRA
class DetalleCompra(models.Model):
    compra = models.ForeignKey('Compra', on_delete=models.CASCADE, related_name='detalles')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='detalles_compra')
    cantidad = models.DecimalField(max_digits=15,decimal_places=2, verbose_name="Cantidad")
    precio_compra = models.BigIntegerField(verbose_name="Precio en Gs.",validators=[MinValueValidator(1)])
    subtotal = models.BigIntegerField()
    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero")
        if self.precio_compra <= 0:
            raise ValidationError("El precio debe ser mayor a cero")

    #Modulo para calcular automaticamente el subtotal
    def save(self, *args, **kwargs):
        self.subtotal = int(round(float(self.cantidad) * self.precio_compra))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.nombre} - {self.cantidad} {self.item.get_unidad_medida_display()}"
#COMPRAS
class Compra(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('ANULADA', 'Anulada'),
    ]
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
    iva_10 = models.BigIntegerField(default=0)
    iva_5 = models.BigIntegerField(default=0)
    total_sin_iva = models.BigIntegerField(default=0)
    total_iva = models.BigIntegerField(default=0)
    monto_total = models.BigIntegerField(default=0)
    estado = models.CharField(max_length=10, choices=[('ACTIVA','Activa'),('ANULADA','Anulada')], default='ACTIVA')
    motivo_anulacion = models.TextField(null=True, blank=True)
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
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
            precio = detalle.precio_compra
            cantidad = float(detalle.cantidad)
            
            if detalle.item.tipo == 'MATERIA_PRIMA':
                # Para 5% IVA incluido: precio_sin_iva = precio / 1.05
                precio_sin_iva = precio / 1.05
                self.total_sin_iva += int(cantidad * precio_sin_iva)
                self.iva_5 += int(cantidad * precio) - int(cantidad * precio_sin_iva)
            elif detalle.item.tipo == 'ARTICULO':
                # Para 10% IVA incluido: precio_sin_iva = precio / 1.10
                precio_sin_iva = precio / 1.10
                self.total_sin_iva += int(cantidad * precio_sin_iva)
                self.iva_10 += int(cantidad * precio) - int(cantidad * precio_sin_iva)

        self.total_iva = self.iva_5 + self.iva_10
        self.monto_total = self.total_sin_iva + self.total_iva
        self.save()

# PRODUCTOS

class CategoriaProducto(models.Model):
    nombre_categ = models.CharField(
    verbose_name="Nombre de categoría",
    max_length=100,
    unique=True
    )

    def __str__(self):
        return self.nombre_categ

class Producto(models.Model):
    ESTADOS = [('A', 'Activo'), ('I', 'Inactivo')
    ]
    codigo = models.CharField(
        verbose_name= 'Código',
        max_length=20,
        unique=True,
    )
    nombre = models.CharField(
        verbose_name='Nombre del producto',
        max_length=100,
        unique=True
    )
    precio = models.PositiveIntegerField(
        verbose_name='Precio',
        validators=[MinValueValidator(1)]
    )
    imagen = models.ImageField(
        verbose_name='Imagen',
        upload_to='producto/',
        blank=True,
        null=True
    )
    descripcion = models.TextField(
        verbose_name="Descripción",
        blank=True,
        max_length=500
    )
    estado = models.CharField(
        verbose_name='Estado',
        max_length=1,
        choices=ESTADOS,
        default='A'
    )
    personalizable = models.BooleanField(default=False)
    
    categoria = models.ForeignKey(
    CategoriaProducto,
        verbose_name='Categoría',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def clean(self):
        super().clean()
        if self.precio == 0:
            raise ValidationError({'precio': 'El precio no puede ser cero.'})

#STOCK
class Stock(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE,related_name='stocks')
    detalle_compra = models.ForeignKey(DetalleCompra,on_delete=models.SET_NULL, null=True, blank=True, related_name='stocks')
    cant_disponible = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cant_minima = models.DecimalField(max_digits=15,decimal_places=2,default=0)
    cant_maxima= models.DecimalField(max_digits=15,decimal_places=2,default=0)
    proveedor_principal = models.ForeignKey(Proveedor, on_delete=models.SET_NULL,null=True, blank=True)
    fecha_ultima_entrada = models.DateField(auto_now_add=True)
    fecha_ultima_salida = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def cantidad_display(self):
        """Devuelve la cantidad en la unidad original para mostrar"""
        if self.item.tipo == 'MATERIA_PRIMA' and self.item.unidad_medida == 'kg':
            return self.cant_disponible/1000
        return self.cant_disponible
    @property
    def precio_unitario(self):
        """Obtiene el precio unitario desde la última compra"""
        if self.detalle_compra:
            return self.detalle_compra.precio_compra

        ultima_compra = DetalleCompra.objects.filter(
            item=self.item
        ).order_by('-compra__fecha').first()

        return ultima_compra.precio_compra if ultima_compra else 0

    @property
    def precio_unitario_display(self):
        """Devuelve el precio en la unidad original para mostrar"""
        if self.item.tipo == 'MATERIA_PRIMA' and self.item.unidad_medida == 'kg':
            return self.precio_unitario * 1000  # Convertir de gramo a kg
        return self.precio_unitario

# Ingredientes - Producto

class IngredienteProducto(models.Model):
    producto = models.ForeignKey(
        'Producto', 
        on_delete=models.CASCADE, 
        related_name='ingredientes', 
        verbose_name="Producto"
        )
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE,
        verbose_name="Ingrediente (Item)"
    )

    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="cantidad en gramos",
        help_text="Cantidad usada en gramos(ej: 150) "
    )

    class Meta:
        unique_together = ('producto', 'item')
        verbose_name = "Ingrediente del producto"

    def __str__(self):
        return f"{self.cantidad}g de {self.item.nombre} para {self.producto.nombre}"