from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from .organization_model import Organization


class UserProfile(models.Model):

    """OS2Webscanner specific user profile.

    Each user MUST be associated with an organization.
    """

    organization = models.ForeignKey(Organization,
                                     null=False,
                                     verbose_name=_('Organization'),
                                     on_delete=models.PROTECT)
    ldap_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.PROTECT,
        related_name='profile',
        verbose_name=_('organisation'),
        default=None,
        null=True
    )
    user = models.OneToOneField(User,
                                related_name='profile',
                                verbose_name=_('User'),
                                on_delete=models.PROTECT)
    is_group_admin = models.BooleanField(default=False)
    is_upload_only = models.BooleanField(default=False)

    @property
    def is_groups_enabled(self):
        """Whether to activate groups in GUI."""
        return settings.DO_USE_GROUPS

    def __str__(self):
        """Return the user's username."""
        return self.user.username
