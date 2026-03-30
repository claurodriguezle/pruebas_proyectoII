from django.db import models

# Clase vacía temporal para evitar errores de importación
class Caja(models.Model):
    class Meta:
        managed = False  # No crea tabla en BD
        
class MovimientoCaja(models.Model):
    class Meta:
        managed = False
        
class VentaPOS(models.Model):
    class Meta:
        managed = False