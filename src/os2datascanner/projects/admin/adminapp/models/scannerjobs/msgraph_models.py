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
import logging

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from mptt.models import TreeManyToManyField
from ....organizations.models.aliases import AliasType

from os2datascanner.engine2.model.msgraph.mail import MSGraphMailSource
from os2datascanner.engine2.model.msgraph.files import MSGraphFilesSource
from os2datascanner.engine2.model.msgraph.calendar import MSGraphCalendarSource
from .scanner_model import Scanner

logger = logging.getLogger(__name__)


def _create_user_list(org_unit, url):  # noqa
    """
    Creates a user list from selected organization units.
    """
    user_list = set()

    for organizational_unit in org_unit.all():
        for position in organizational_unit.position_set.all():
            addresses = position.account.aliases.filter(
                _alias_type=AliasType.EMAIL.value,
            )
            if not addresses:
                logger.info(
                    f"user {position.account.username} has no email alias "
                    "connected"
                )
            else:
                for alias in addresses:
                    address = alias.value
                    if address.endswith(url):
                        user_list.add(address)

    logger.info(f"submitting scan for accounts {', '.join(user_list)}")

    return frozenset(user_list)


class MSGraphScanner(Scanner):
    tenant_id = models.CharField(max_length=256, verbose_name="Tenant ID",
                                 null=False)

    class Meta:
        abstract = True


class MSGraphMailScanner(MSGraphScanner):
    org_unit = TreeManyToManyField(
        "organizations.OrganizationalUnit",
        related_name="msgraphmailscanners",
        blank=True,
        verbose_name=_("organizational unit"),
    )

    def get_type(self):
        return 'msgraph-mail'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/msgraph-mailscanners/'

    def generate_sources(self):  # noqa
        if not self.org_unit.exists():
            # If no organizational units have been selected
            # yield one source.
            yield MSGraphMailSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=self.tenant_id,
                client_secret=settings.MSGRAPH_CLIENT_SECRET
            )
        else:
            # Otherwise yield a source for every user
            # in the selected organizational unit(s).
            yield MSGraphMailSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=self.tenant_id,
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                userlist=_create_user_list(self.org_unit, self.url),
            )


class MSGraphFileScanner(MSGraphScanner):
    scan_site_drives = models.BooleanField(
            default=True, verbose_name='Scan alle SharePoint-mapper')
    scan_user_drives = models.BooleanField(
            default=True, verbose_name='Scan alle OneDrive-drev')
    org_unit = TreeManyToManyField(
        "organizations.OrganizationalUnit",
        related_name="msgraphfilescanners",
        blank=True,
        verbose_name=_("organizational unit"),
    )

    def get_type(self):
        return 'msgraph-file'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/msgraph-filescanners/'

    def generate_sources(self):  # noqa
        if not self.org_unit.exists():
            # If no organizational units have been selected
            # yield one source.
            yield MSGraphFilesSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=self.tenant_id,
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                site_drives=self.scan_site_drives,
                user_drives=self.scan_user_drives
            )
        else:
            # Otherwise yield a source for every user
            # in the selected organizational unit(s).
            yield MSGraphFilesSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=self.tenant_id,
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                site_drives=self.scan_site_drives,
                user_drives=self.scan_user_drives,
                userlist=_create_user_list(self.org_unit, self.url),
            )


class MSGraphCalendarScanner(MSGraphScanner):
    """Model for MSGraphCalendarSource."""
    org_unit = TreeManyToManyField(
        "organizations.OrganizationalUnit",
        related_name="msgraphcalendarscanners",
        blank=True,
        verbose_name=_("organizational unit"),
    )

    def get_type(self):
        return 'msgraph-calendar'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/msgraph-calendarscanners/'

    def generate_sources(self):  # noqa
        if not self.org_unit.exists():
            # If no organizational units have been selected
            # yield one source.
            yield MSGraphCalendarSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=self.tenant_id,
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
            )
        else:
            # Otherwise yield a source for every user
            # in the selected organizational unit(s).
            yield MSGraphCalendarSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=self.tenant_id,
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                userlist=_create_user_list(self.org_unit, self.url)
            )
