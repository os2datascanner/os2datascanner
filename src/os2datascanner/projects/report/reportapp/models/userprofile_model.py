from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from .organization_model import Organization


class UserProfile(models.Model):

    organization = models.ForeignKey(Organization,
                                     null=True, blank=True,
                                     verbose_name='Organisation',
                                     on_delete=models.PROTECT)
    user = models.OneToOneField(User,
                                related_name='profile',
                                verbose_name='Bruger',
                                on_delete=models.PROTECT)

    def __str__(self):
        """Return the user's username."""
        return self.user.username
