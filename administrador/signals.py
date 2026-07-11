from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Persona, Cliente

@receiver(post_save, sender=Persona)
def sync_correo_a_user(sender, instance, **kwargs):
    # instance = la Persona que se acaba de guardar
    try:
        cliente = instance.cliente
    except Cliente.DoesNotExist:
        return

    if cliente.user and cliente.user.email != instance.correo:
        cliente.user.email = instance.correo
        cliente.user.save(update_fields=['email'])