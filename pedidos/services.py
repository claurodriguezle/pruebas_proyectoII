import math

# Coordenadas fijas del negocio

NEGOCIO_LATITUD = -25.460214108638066
NEGOCIO_LONGITUD = -56.440428219528705

RADIO_MAXIMO_KM = 5

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en km entre dos coordenadas geograficas usuando la formula de Haversine.
    """
    R = 6371 # Radio de la Tierra en KM

    lat1, lon1, lat2, lon2 = map(math.radians, [
        float(lat1), float(lon1),
        float(lat2), float(lon2)
    ])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c # Resultado en km

def calcular_costo_delivery(distancia_km):
    """
    Calcula el costo del delivery segun la distancia
    - 0 a 3 km: 7.000gs
    - 3 a 5 km: 10.000gs
    """
    if distancia_km <= 3:
        return 7000
    else:
        return 10000

def validar_delivery(direccion):
    """
    Valida si una direccion es elegible para delivery.
    Retorna un dict con el resultado y un mensaje.
    """

    # Paso 1: Validar si el barrio esta habilitado

    if not direccion.barrio:
        return {
            "disponible": False,
            "mensaje": "La dirección no tiene un barrio asignado."
        }
    
    if not direccion.barrio.habilitado:
        return {
            "disponible": False,
            "mensaje": f"El delivey no está disponible por el momento en el barrio {direccion.barrio.nombre}."
        }
    
    # Paso 2: Validar si tiene coordenadas
    if not direccion.latitud or not direccion.longitud:
        return {
            "disponible": False,
            "mensaje": "La dirección no tiene coordenas registradas."
        }
    
    # Paso 3: Calcular distancia
    distancia = calcular_distancia_haversine(
        NEGOCIO_LATITUD, NEGOCIO_LONGITUD,
        direccion.latitud, direccion.longitud
    )

    if distancia > RADIO_MAXIMO_KM:
        return {
            "disponible": False,
            "mensaje": f"Tu dirección esta a {distancia:.1f} km. El radio máximo de entrega es de {RADIO_MAXIMO_KM}."
        }
    
    # Paso 4: Calcular costo
    costo = calcular_costo_delivery(distancia)
    
    return {
        "disponible": True,
        "mensaje": f"Delivey disponible. Distancia: {distancia:1f} km.",
        "distancia_km": round(distancia, 2),
        "costo_delivery": costo
    }