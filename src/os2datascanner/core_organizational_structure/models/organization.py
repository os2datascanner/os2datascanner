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
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator

from ..serializer import BaseSerializer


class StatisticsPageConfigChoices(models.TextChoices):
    MANAGERS = "M", "Managers"
    DPOS = "D", "Data Protection Officers"
    SUPERUSERS = "S", "Superusers"
    NONE = "N", "None"


class SupportContactChoices(models.TextChoices):
    NONE = "NO", _("None")
    WEBSITE = "WS", _("Website")
    EMAIL = "EM", _("Email")


class DPOContactChoices(models.TextChoices):
    NONE = "NO", _("None")
    SINGLE_DPO = "SD", _("Single DPO")
    UNIT_DPO = "UD", _("Unit DPO")


class MSGraphWritePermissionChoices(models.TextChoices):
    CATEGORIZE = "CAT", _("Categorize emails")
    DELETE = "DEL", _("Delete emails")
    ALL = "ALL", _("Permit all")
    NONE = "NON", _("No permissions")


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
    msgraph_write_permissions = models.CharField(
        max_length=3,
        choices=MSGraphWritePermissionChoices.choices,
        default=MSGraphWritePermissionChoices.NONE,
        verbose_name=_('MSGraph write permissions'),
        help_text=_('Select permission(s) you wish to allow for your organization.')
    )

    # Access settings
    leadertab_access = models.CharField(
        max_length=1,
        choices=StatisticsPageConfigChoices.choices,
        default=StatisticsPageConfigChoices.MANAGERS,
        verbose_name=_("Leadertab access")
    )
    dpotab_access = models.CharField(
        max_length=1,
        choices=StatisticsPageConfigChoices.choices,
        default=StatisticsPageConfigChoices.DPOS,
        verbose_name=_("Dpotab access")
    )

    # Support button settings
    show_support_button = models.BooleanField(
        default=False, verbose_name=_("show support button"))
    support_contact_method = models.CharField(
        max_length=2,
        choices=SupportContactChoices.choices,
        default=SupportContactChoices.NONE,
        verbose_name=_("support contact method"),
        blank=True
    )
    support_name = models.CharField(
        max_length=100, default="IT",
        blank=True, verbose_name=_("support name"))
    support_value = models.CharField(
        max_length=1000, default="",
        blank=True, verbose_name=_("support value"))
    dpo_contact_method = models.CharField(
        max_length=2,
        choices=DPOContactChoices.choices,
        default=DPOContactChoices.NONE,
        verbose_name=_("DPO contact method"),
        blank=True
    )
    dpo_name = models.CharField(
        max_length=100, default="",
        blank=True, verbose_name=_("DPO name"))
    dpo_value = models.CharField(
        max_length=100, default="",
        blank=True, verbose_name=_("DPO value"))

    def clean(self):
        errors = {}

        # Validate support contact value based on the type
        if self.support_contact_method == SupportContactChoices.WEBSITE:
            validator = URLValidator()
        elif self.support_contact_method == SupportContactChoices.EMAIL:
            validator = EmailValidator()
        if self.support_contact_method in (
                SupportContactChoices.EMAIL,
                SupportContactChoices.WEBSITE):
            if not self.support_name:
                errors['support_name'] = _("Provide a name of the support contact.")
            try:
                validator(self.support_value)
            except Exception as e:
                errors['support_value'] = e

        if self.dpo_contact_method == DPOContactChoices.SINGLE_DPO:
            if not self.dpo_name:
                errors['dpo_name'] = _("Provide a name of the DPO.")

            try:
                EmailValidator()(self.dpo_value)
            except Exception as e:
                errors['dpo_value'] = e

        if errors:
            raise ValidationError(errors)

        return super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

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
                  'show_support_button', 'support_contact_method', 'support_name',
                  'support_value', 'dpo_contact_method', 'dpo_name', 'dpo_value',
                  'msgraph_write_permissions']
