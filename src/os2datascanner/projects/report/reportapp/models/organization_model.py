from django.db import models
from django.conf import settings
import uuid

class Organization(models.Model):

    """Represents the organization for each user and scanner, etc.

    Users can only see material related to their own organization.

    This is a read-only model synchronized from the admin module.
    """

    name = models.CharField(max_length=256, unique=True, verbose_name='Navn', 
                            editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        """Return the name of the organization."""
        return self.name
