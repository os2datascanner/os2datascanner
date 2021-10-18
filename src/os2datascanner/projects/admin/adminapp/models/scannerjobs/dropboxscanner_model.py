# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2.eu/ )
import structlog
from django.db import models
from django.core.validators import MinLengthValidator

from os2datascanner.engine2.model.dropbox import DropboxSource
from .scanner_model import Scanner

# Get an instance of a logger
logger = structlog.get_logger()


class DropboxScanner(Scanner):

    """File scanner for scanning network drives and folders"""

    token = models.CharField(
        max_length=64,
        verbose_name='Token',
        null=True,
        validators=[MinLengthValidator(64)])

    def __str__(self):
        """Return the URL for the scanner."""
        return self.url

    def get_type(self):
        return 'dropbox'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/dropboxscanners/'

    def make_engine2_source(self):
        return DropboxSource(
            self.token)
