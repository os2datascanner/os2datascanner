from django.db import models
from django.conf import settings
from uuid import uuid4


class Organization(models.Model):
    """Represents the organization for each user and scanner, etc.

    Users can only see material related to their own organization.
    """

    name = models.CharField(max_length=256, unique=True, verbose_name='Navn')
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name='Telefon')
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
