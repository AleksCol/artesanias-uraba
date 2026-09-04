from django import template

from catalogo.formato import formato_de_pesos

register = template.Library()

register.filter("pesos", formato_de_pesos)
