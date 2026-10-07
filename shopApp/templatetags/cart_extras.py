from django import template
from decimal import Decimal

register = template.Library()


@register.filter(name="money")
def money(value):
    try:
        value = Decimal(str(value))
    except Exception:
        return value
    return f"{value:,.2f}"