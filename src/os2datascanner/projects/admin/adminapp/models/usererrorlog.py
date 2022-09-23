from django.db import models
from django.utils.translation import ugettext_lazy as _

from .scannerjobs.scanner import ScanStatus
from ...organizations.models.organization import Organization


translation_table = {
    "Exploration error. MemoryError: 12, Cannot allocate memory":
    _("Folder at the path is using outdated encoding. Please "
      "rename the folder."),
    "Exploration error. ValueError: Source could not be opened (perhaps corrupt content)":
    _("An object was skipped either because it could not be opened or "
      "it was taking too long to scan."),
}


class UserErrorLog(models.Model):

    """Model for logging errors relevant for the user."""

    scan_status = models.ForeignKey(
        ScanStatus,
        on_delete=models.CASCADE,
        verbose_name=_('scan status')
    )
    path = models.CharField(
        max_length=1024,
        verbose_name=_('Path'),
        blank=True
    )
    error_message = models.CharField(
        max_length=1024,
        verbose_name=_('Error message')
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='usererrorlog',
        verbose_name=_('organization'),
        null=True
    )
    is_new = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)

    @property
    def user_friendly_error_message(self):
        """Translates an error message into a meaningful instruction
        for the user, if one is available."""
        if self.error_message in translation_table.keys():
            return translation_table[self.error_message]
        else:
            return self.error_message
