from django.apps import AppConfig
from django.utils.translation import pgettext_lazy


class CoreConfig(AppConfig):
    name = 'os2datascanner.projects.admin.core'
    label = 'core'
    verbose_name = pgettext_lazy('Verbose name for core app', 'Management')
    default = True
