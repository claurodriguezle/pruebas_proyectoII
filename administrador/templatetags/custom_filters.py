from django import template
# Filtros personalizados, cambia la coma por un punto en los precios
register = template.Library()

@register.filter
def punto_miles(value):
    return str(value).replace(",", ".")
