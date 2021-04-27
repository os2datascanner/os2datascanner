from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ImportServicesConfig(AppConfig):
    name = 'os2datascanner.projects.admin.import_services'
    label = 'import_services'
    verbose_name = _('import services')
