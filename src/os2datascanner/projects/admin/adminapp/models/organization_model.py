from uuid import uuid4

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class Organization(models.Model):
    """Represents the organization for each user and scanner, etc.

    Users can only see material related to their own organization.
    """

    name = models.CharField(max_length=256, unique=True, verbose_name=_('Name'))
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name=_('Phone'))
    do_use_groups = models.BooleanField(default=False,
                                        editable=settings.DO_USE_GROUPS)
    do_notify_all_scans = models.BooleanField(default=True)
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True,
                            verbose_name="UUID")

    def __str__(self):
        """Return the name of the organization."""
        return self.name

    def to_json_object(self):
        """JSON-ready dict-representation of the object"""
        return {
            "name": self.name,
            "uuid": str(self.uuid),
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "do_use_groups": self.do_use_groups,
            "do_notify_all_scans": self.do_notify_all_scans,
        }

    class DatascannerMeta:
        broadcast_change_events = True


class APIKey(models.Model):
    """An APIKey can be used to give an external service access to parts of the
    administration system's API on behalf of a specific organization."""
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False,
                            unique=True, verbose_name="UUID")
    organization = models.ForeignKey(Organization, null=False,
                                     related_name="api_keys",
                                     on_delete=models.PROTECT,
                                     verbose_name=_('organization - deprecated'))
    ldap_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.PROTECT,
        related_name='api_keys',
        verbose_name=_('organization'),
        default=None,
        null=True,
    )
    """A newline-separated list of API functions that can be called with this
    API key."""
    scope = models.TextField()

    def __contains__(self, function):
        """Indicates whether or not the named function can be called with this
        API key."""
        return function in self.scope.splitlines()

    class Meta:
        verbose_name = _("API key")
        verbose_name_plural = _('API keys')
