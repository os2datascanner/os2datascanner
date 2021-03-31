from django.db import models
from django.utils.translation import ugettext_lazy as _

from .organization_model import Organization
from .userprofile_model import UserProfile


class Group(models.Model):
    """Represents the group or sub-organisation."""
    name = models.CharField(max_length=256, unique=True, verbose_name=_('Name'))
    contact_email = models.CharField(max_length=256, verbose_name='Email')
    contact_phone = models.CharField(max_length=256, verbose_name=_('Phone'))
    user_profiles = models.ManyToManyField(UserProfile, blank=True,
                                           verbose_name=_('Users'),
                                           related_name='groups')
    organization = models.ForeignKey(Organization,
                                     null=False,
                                     related_name='groups',
                                     verbose_name=_('Organization'),
                                     on_delete=models.PROTECT)

    def __str__(self):
        """Return the name of the group."""
        return self.name

    class Meta:
        """Ordering and other options."""
        ordering = ['name']

    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return "Group '%s'" % self
