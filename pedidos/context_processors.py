# pedidos/context_processors.py
from caja.models import Caja

def caja_abierta(request):
    """Context processor para saber si la caja está abierta desde cualquier template"""
    caja = Caja.objects.filter(estado='abierta').first()
    return {
        'caja_abierta': caja is not None,
        'caja_actual': caja,
    }