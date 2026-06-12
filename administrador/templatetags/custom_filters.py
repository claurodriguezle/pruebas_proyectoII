from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def punto_miles(value):
    """Enteros con punto como separador de miles. Ej: 12500 → 12.500"""
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value

@register.filter  
def numero_py(value):
    try:
        if isinstance(value, str):
            # Quitar puntos de miles y convertir coma decimal a punto
            value = value.replace(".", "").replace(",", ".")
        d = Decimal(str(value))
        sign, digits, exponent = d.normalize().as_tuple()

        if exponent >= 0:
            return f"{int(d):,}".replace(",", ".")
        else:
            decimales = abs(exponent)
            formatted = f"{d:,.{decimales}f}"
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value
