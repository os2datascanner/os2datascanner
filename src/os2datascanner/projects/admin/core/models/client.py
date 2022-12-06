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
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#

from uuid import uuid4

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .utilities import ModelChoiceFlag


class Scan(ModelChoiceFlag):
    """Enumeration of available scan types"""
    # Ints are given explicitly to allow reorganization without database issues
    WEBSCAN = (1 << 0, _('web scan'))
    FILESCAN = (1 << 1, _('file scan'))
    EXCHANGESCAN = (1 << 2, _('Exchange scan'))
    SBSYSSCAN = (1 << 3, _('SBSYS scan'))
    DROPBOXSCAN = (1 << 4, _('Dropbox scan'))
    MSGRAPH_MAILSCAN = (1 << 5, _('Microsoft Graph - mail scan'))
    MSGRAPH_FILESCAN = (1 << 6, _('Microsoft Graph - file scan'))
    GOOGLE_DRIVESCAN = (1 << 7, _('Google - drive scan'))
    GOOGLE_MAILSCAN = (1 << 8, _('Google - mail scan'))
    # NB! Int value must not exceed 2,147,483,647 (limited by the db field)
    # Thus a maximum of 31 scan types in one Flag class


class Feature(ModelChoiceFlag):
    """Enumeration of available features."""
    ADMIN_API = (1, _('administration API'))
    # To ease the transition from the old `adminapp.Organization` to the new
    # `organizations.Organization`, the feature flag below is provided. It
    # allows the activation (or deactivation, depending on state) of the other
    # models and features in the `organizations` app; existing customers may
    # thus be migrated "silently" to the new `Organization` without being
    # overwhelmed by additional features.
    ORG_STRUCTURE = (1 << 1, _('structured organization support'))
    IMPORT_SERVICES = (1 << 2, _('import services'))
    IMPORT_SERVICES_MS_GRAPH = (1 << 3, _('import services (MS Graph)'))
    IMPORT_SERVICES_OS2MO = (1 << 4, _('import services (OS2mo)'))


class Client(models.Model):
    """Stores data for a specific client.

    A Clients is identified by a uuid and further stores a human readable name,
    contact information (email and phone number), and flags representing the
    activated features and enabled scan types for that Client.

    In a multi-tenant system, any Client should only be able to access and
    manage resources owned by that Client.
    """

    uuid = models.UUIDField(
        default=uuid4,
        primary_key=True,
        editable=False,
        verbose_name=_('client ID'),
    )
    name = models.CharField(
        max_length=256,
        unique=True,
        verbose_name=_('name'),
    )
    contact_email = models.CharField(
        max_length=256,
        verbose_name=_('e-mail'),
    )
    contact_phone = models.CharField(
        max_length=32,
        verbose_name=_('phone number'),
    )

    features = models.PositiveIntegerField(
        default=0,
        validators=[Feature.validator],
        verbose_name=_('enabled features'),
    )

    scans = models.PositiveIntegerField(
        default=0,
        validators=[Scan.validator],
        verbose_name=_('activated scan types'),
    )

    @property
    def enabled_features(self):
        return Feature(self.features)

    @enabled_features.setter
    def enabled_features(self, flag_enum):
        self.features = flag_enum.value

    @property
    def activated_scan_types(self):
        return Scan(self.scans)

    @activated_scan_types.setter
    def activated_scan_types(self, flag_enum):
        self.scans = flag_enum.value

    class Meta:
        verbose_name = _('client')
        verbose_name_plural = _('clients')

    def __str__(self):
        """Return the name of the client"""
        return self.name

    def __repr__(self):
        """Return the id and name of the client"""
        return f"<{self.__class__.__name__}: {self.name} ({self.uuid})>"
