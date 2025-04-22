from django.db import models

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
    ruc = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        default=None
        )

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
    ruc = models.CharField(
        max_length=20, 
        unique=True,
        blank=True,
        null=True,
        default=None
        )

    def __str__(self):
        return f"Proveedor: {self.nombre_empresa}"

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

  precio = models.DecimalField(
    verbose_name='Precio',
    max_digits=10,
    decimal_places=2
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

  categoria = models.ForeignKey(
    CategoriaProducto,
    verbose_name='Categoría',
    on_delete=models.SET_NULL,
    null=True,
    blank=True
  )

  def __str__(self):
    return f"{self.codigo} - {self.nombre}"