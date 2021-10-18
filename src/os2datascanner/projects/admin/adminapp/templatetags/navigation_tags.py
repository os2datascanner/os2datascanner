from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag()
def report_module_url():
    return settings.REPORT_URL
