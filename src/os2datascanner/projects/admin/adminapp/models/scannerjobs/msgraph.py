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
from django.utils.translation import gettext_lazy as _

from os2datascanner.engine2.model.msgraph.mail import MSGraphMailSource
from os2datascanner.engine2.model.msgraph.files import MSGraphFilesSource
from os2datascanner.engine2.model.msgraph.calendar import MSGraphCalendarSource
from os2datascanner.engine2.model.msgraph.teams import MSGraphTeamsFilesSource

from ....organizations.models.aliases import AliasType
from ....grants.models import GraphGrant
from .scanner import Scanner

logger = logging.getLogger(__name__)


def _create_user_list(org_unit):  # noqa
    """
    Creates a user list from selected organization units.
    """
    user_list = set()

    for organizational_unit in org_unit.all():
        for position in organizational_unit.positions.all():
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
                    user_list.add(address)

    logger.info(f"submitting scan for accounts {', '.join(user_list)}")

    return frozenset(user_list)


class MSGraphScanner(Scanner):
    grant = models.ForeignKey(GraphGrant, null=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True
        ordering = ['name']


class MSGraphMailScanner(MSGraphScanner):
    scan_deleted_items_folder = models.BooleanField(
        default=False,
        verbose_name=_('Scan deleted items folder'),
        help_text=_("Include emails in the deleted post folder"),
    )

    scan_syncissues_folder = models.BooleanField(
        default=True,
        verbose_name=_('Scan syncissues folder'),
        help_text=_("Include emails in the syncissues folder"),
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
                tenant_id=str(self.grant.tenant_id),
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                scan_deleted_items_folder=self.scan_deleted_items_folder,
                scan_syncissues_folder=self.scan_syncissues_folder
            )
        else:
            # Otherwise yield a source for every user
            # in the selected organizational unit(s).
            yield MSGraphMailSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=str(self.grant.tenant_id),
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                userlist=_create_user_list(self.org_unit),
                scan_deleted_items_folder=self.scan_deleted_items_folder,
                scan_syncissues_folder=self.scan_syncissues_folder
            )


class MSGraphFileScanner(MSGraphScanner):
    scan_site_drives = models.BooleanField(
            default=True, verbose_name='Scan alle SharePoint-mapper')
    scan_user_drives = models.BooleanField(
            default=True, verbose_name='Scan alle OneDrive-drev')

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
                tenant_id=str(self.grant.tenant_id),
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                site_drives=self.scan_site_drives,
                user_drives=self.scan_user_drives
            )
        else:
            # Otherwise yield a source for every user
            # in the selected organizational unit(s).
            yield MSGraphFilesSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=str(self.grant.tenant_id),
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                site_drives=self.scan_site_drives,
                user_drives=self.scan_user_drives,
                userlist=_create_user_list(self.org_unit),
            )


class MSGraphCalendarScanner(MSGraphScanner):
    """Model for MSGraphCalendarSource."""

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
                tenant_id=str(self.grant.tenant_id),
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
            )
        else:
            # Otherwise yield a source for every user
            # in the selected organizational unit(s).
            yield MSGraphCalendarSource(
                client_id=settings.MSGRAPH_APP_ID,
                tenant_id=str(self.grant.tenant_id),
                client_secret=settings.MSGRAPH_CLIENT_SECRET,
                userlist=_create_user_list(self.org_unit)
            )


class MSGraphTeamsFileScanner(MSGraphScanner):

    linkable = True

    do_link_check = models.BooleanField(
        default=False,
        verbose_name=_("check dead links")
    )

    def get_type(self):
        return 'msgraph-teams-file'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/msgraph-teams-filescanners/'

    def generate_sources(self):

        yield MSGraphTeamsFilesSource(
            client_id=settings.MSGRAPH_APP_ID,
            tenant_id=str(self.grant.tenant_id),
            client_secret=settings.MSGRAPH_CLIENT_SECRET,
        )
