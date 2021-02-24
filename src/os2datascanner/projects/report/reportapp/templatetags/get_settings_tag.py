from django import template
from django.conf import settings

register = template.Library()


# Allows to get access to a settings value in a template.
@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")
