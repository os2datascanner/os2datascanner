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
from recurrence.fields import RecurrenceField
from uuid import uuid4

from django.db import models
from django.utils.translation import gettext_lazy as _

from ..serializer import BaseSerializer


class StatisticsPageConfigChoices(models.TextChoices):
    MANAGERS = "M", "Managers"
    DPOS = "D", "Data Protection Officers"
    SUPERUSERS = "S", "Superusers"
    NONE = "N", "None"


class SupportContactStyles(models.TextChoices):
    NONE = "NO", _("None")
    WEBSITE = "WS", _("Website")
    EMAIL = "EM", _("Email")


class DPOContactStyles(models.TextChoices):
    NONE = "NO", _("None")
    SINGLE_DPO = "SD", _("Single DPO")
    UNIT_DPO = "UD", _("Unit DPO")


class Organization(models.Model):
    """Stores data for a specific organization.

    An Organization represents the administrative context for a self-contained
    organization, with an optional reference to a representation of its
    hierarchical structure.

    Note that the system distinguishes between Client and Organization. This
    is to allow the case where one Client (e.g. a service provider) administers
    scans for several Organizations.

    All Organizations are related to exactly one Client.
    """

    serializer_class = None

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name=_('UUID'),
    )
    name = models.CharField(
        max_length=256,
        verbose_name=_('name'),
    )
    contact_email = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name=_('email'),
    )
    contact_phone = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name=_('phone number'),
    )

    email_notification_schedule = RecurrenceField(
        max_length=1024,
        null=True,
        blank=True,
        default="RRULE:FREQ=WEEKLY;BYDAY=FR",
        verbose_name=_('Email notification interval')
    )

    # Access settings
    leadertab_access = models.CharField(
        max_length=1,
        choices=StatisticsPageConfigChoices.choices,
        default=StatisticsPageConfigChoices.MANAGERS,
    )
    dpotab_access = models.CharField(
        max_length=1,
        choices=StatisticsPageConfigChoices.choices,
        default=StatisticsPageConfigChoices.DPOS,
    )

    # Support button settings
    show_support_button = models.BooleanField(
        default=False, verbose_name=_("show support button"))
    support_contact_style = models.CharField(
        max_length=2,
        choices=SupportContactStyles.choices,
        default=SupportContactStyles.NONE,
        verbose_name=_("support contact style")
    )
    support_name = models.CharField(
        max_length=100, default="IT",
        blank=True, verbose_name=_("support name"))
    support_value = models.CharField(
        max_length=1000, default="",
        blank=True, verbose_name=_("support value"))
    dpo_contact_style = models.CharField(
        max_length=2,
        choices=DPOContactStyles.choices,
        default=DPOContactStyles.NONE,
        verbose_name=_("DPO contact style")
    )
    dpo_name = models.CharField(
        max_length=100, default="",
        blank=True, verbose_name=_("DPO name"))
    dpo_value = models.CharField(
        max_length=100, default="",
        blank=True, verbose_name=_("DPO value"))

    class Meta:
        abstract = True
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.uuid})>"


class OrganizationSerializer(BaseSerializer):
    class Meta:
        fields = ['pk', 'name', 'contact_email', 'contact_phone',
                  'email_notification_schedule', 'leadertab_access', 'dpotab_access',
                  'show_support_button', 'support_contact_style', 'support_name',
                  'support_value', 'dpo_contact_style', 'dpo_name', 'dpo_value']
