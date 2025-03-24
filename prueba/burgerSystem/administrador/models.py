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
    ruc = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"Cliente: {self.nombre} {self.apellido}"