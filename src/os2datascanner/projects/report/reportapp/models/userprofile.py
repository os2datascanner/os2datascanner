from django.db import models
from django.contrib.auth.models import User

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.projects.report.organizations.models import Organization


class UserProfile(models.Model):

    organization = models.ForeignKey(Organization,
                                     null=True, blank=True,
                                     verbose_name='Organisation',
                                     on_delete=models.PROTECT)
    user = models.OneToOneField(User,
                                related_name='profile',
                                verbose_name='Bruger',
                                on_delete=models.PROTECT)
    last_handle = models.DateTimeField(verbose_name='Sidste håndtering',
                                       null=True, blank=True)

    def __str__(self):
        """Return the user's username."""
        return self.user.username

    def update_last_handle(self):
        self.last_handle = time_now()
        self.save()

    @property
    def time_since_last_handle(self):
        return (time_now() - self.last_handle).total_seconds() if self.last_handle else 60*60*24*3
