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
import os

from django.db import models
from django.conf import settings

from .scanner_model import Scanner


class MSGraphScanner(Scanner):
    tenant_id = models.CharField(max_length=256, verbose_name="Tenant ID",
                                 null=False)

    class Meta:
        abstract = True


class MSGraphMailScanner(MSGraphScanner):
    def get_type(self):
        return 'msgraph-mail'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/msgraph-mailscanners/'

    def generate_sources(self):
        yield from []
