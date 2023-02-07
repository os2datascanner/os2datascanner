from django import template

register = template.Library()


@register.filter
def unique_roots(qs):
    return set([unit.get_root() for unit in qs])
