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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

import structlog
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from os2datascanner.engine2.model.smbc import SMBCSource
from .scanner import Scanner

# Get an instance of a logger
logger = structlog.get_logger()


class FileScanner(Scanner):

    """File scanner for scanning network drives and folders"""

    unc = models.CharField(max_length=2048, blank=False, verbose_name='UNC')
    alias = models.CharField(
        max_length=64,
        verbose_name=_("drive letter"),
        null=True)
    skip_super_hidden = models.BooleanField(
        verbose_name=_("skip super-hidden files"),
        help_text=_("do not scan files with the HIDDEN and SYSTEM bits"
                    " set, or files with the HIDDEN bit set whose name"
                    " starts with a tilde"),
        default=False)

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.unc.replace('*.', '')
        return url

    @property
    def needs_revalidation(self):
        try:
            return self.objects.get(pk=self.pk).unc != self.unc
        except FileScanner.DoesNotExist:
            return False

    def __str__(self):
        """Return the URL for the scanner."""
        return self.unc

    def get_type(self):
        return 'file'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/filescanners/'

    def generate_sources(self):
        yield SMBCSource(
                self.unc,
                user=self.authentication.username,
                password=self.authentication.get_password(),
                domain=self.authentication.domain,
                driveletter=self.alias,
                skip_super_hidden=self.skip_super_hidden)

    def clean(self):
        # Backslashes (\) are an escaped character and therefore '\\\\' = '\\'
        if not self.unc.startswith(('//', '\\\\')) or any(x in self.unc for x in ['\\\\\\', '///']):
            error = _("UNC must follow the UNC format")
            raise ValidationError({"unc": error})
