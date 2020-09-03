from django.db import models
from django.conf import settings

from os2datascanner.engine2.model.googledrive import GoogleDriveSource
from .scanner_model import Scanner


class GoogleDriveScanner(Scanner):
    """File scanner for scanning google drive"""
    access_code = models.CharField(max_length=256, verbose_name="Access Code", null=True)

    def __str__(self):
        """Return the URL for the scanner."""
        return self.url

    def get_type(self):
        return 'googledrive'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/googledrivescanners'

    def generate_sources(self):
        yield GoogleDriveSource(access_code=self.access_code)