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

