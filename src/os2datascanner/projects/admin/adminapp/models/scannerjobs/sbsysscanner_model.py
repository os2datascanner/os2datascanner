from django.db import models
from django.conf import settings

from .scanner_model import Scanner

class SbsysScanner(Scanner):
    def get_type(self):
        return 'sbsys'

    def get_absolute_url(self):
        return '/sbsysscanners'