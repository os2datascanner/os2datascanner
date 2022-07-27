from uuid import uuid4

from django.db import models
from django.utils.translation import ugettext_lazy as _


class APIKey(models.Model):
    """An APIKey can be used to give an external service access to parts of the
    administration system's API on behalf of a specific organization."""
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False,
                            unique=True, verbose_name="UUID")
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name=_('organization'),
        default=None,
        null=True,
    )
    # A newline-separated list of API functions that can be called with this
    # API key.
    scope = models.TextField()

    def __contains__(self, function):
        """Indicates whether or not the named function can be called with this
        API key."""
        return function in self.scope.splitlines()

    class Meta:
        verbose_name = _("API key")
        verbose_name_plural = _('API keys')
