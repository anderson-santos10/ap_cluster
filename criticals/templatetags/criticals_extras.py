from django import template

register = template.Library()


@register.filter
def has_edge_space(value):
    text = "" if value is None else str(value)
    return text != text.strip()
