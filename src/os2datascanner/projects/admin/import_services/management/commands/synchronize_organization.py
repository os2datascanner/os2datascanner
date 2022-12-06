#!/usr/bin/env python
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
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )
import logging
from django.core.management import BaseCommand

from os2datascanner.projects.admin.import_services.models import ImportService
from os2datascanner.projects.admin.import_services.models import LDAPConfig
from os2datascanner.projects.admin.import_services.models import MSGraphConfiguration
from os2datascanner.projects.admin.import_services.models import OS2moConfiguration
from os2datascanner.projects.admin.import_services.utils import start_ldap_import, \
    start_msgraph_import, start_os2mo_import

"""
    This command should be run by a cron job at the desired time
    organizational synchronizations should take place.
"""

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Run organization synchronization for current configured type(s):"

    def handle(self, *args, **kwargs):
        for conf in ImportService.objects.select_subclasses().all():
            if isinstance(conf, LDAPConfig):
                start_ldap_import(conf)
            elif isinstance(conf, MSGraphConfiguration):
                start_msgraph_import(conf)
            elif isinstance(conf, OS2moConfiguration):
                start_os2mo_import(conf)
            else:
                logger.warning(f"ignoring unknown import service {type(conf).__name__}")
