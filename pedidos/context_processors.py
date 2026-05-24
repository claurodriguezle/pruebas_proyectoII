from pedidos.views import local_esta_abierto
 
def caja_abierta(request):
    """Context processor: indica si el local está dentro del horario de atención."""
    abierto = local_esta_abierto()
    return {
        'caja_abierta': abierto,
        'caja_actual': None,  # ya no se usa la caja para el flujo online
    }