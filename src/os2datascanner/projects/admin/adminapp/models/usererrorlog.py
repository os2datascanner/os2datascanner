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

    class Meta:
        verbose_name = _('error log')
        verbose_name_plural = _('error logs')

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
    engine_error = models.JSONField(
        blank=True,
        null=True
    )
    # {
    #     "type": "UnavailableError",
    #     "args": ["www.example.invalid.doesnotexist"]
    # }
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='usererrorlog',
        verbose_name=_('organization'),
        null=True
    )
    is_new = models.BooleanField(
        default=False,
        verbose_name=_('Is new')
    )
    is_removed = models.BooleanField(
        default=False,
        verbose_name=_('Is removed')
    )

    @property
    def user_friendly_error_message(self):
        """Translates an error message into a meaningful instruction
        for the user, if one is available."""
        if self.engine_error:
            args = self.engine_error.get("args")
            if self.engine_error.get("type") == "UnavailableError":
                return _("Could not open a connection to {0}".format(args[0]))

        if self.error_message in translation_table.keys():
            return translation_table[self.error_message]
        else:
            return self.error_message
    user_friendly_error_message.fget.short_description = _('User friendly error message')

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.path} | "\
            f"{self.error_message} ({self.organization})>"
