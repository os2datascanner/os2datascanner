from ..models.scannerjobs.gmail_model import GmailScanner
from .scanner_views import *


class GmailScannerList(ScannerList):
    """Displays a list of file scanners."""
    model = GmailScanner
    type = 'gmail'


class GmailScannerCreate(ScannerCreate):
    """Create a scanner view"""

    model = GmailScanner
    fields = [
        'name',
        'schedule',
        'service_account_file_gmail',
        'user_emails_gmail',
        'exclusion_rules',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/gmailscanners/%s/created/' % self.object.pk


class GmailScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = GmailScanner
    fields = [
        'name',
        'schedule',
        'service_account_file_gmail',
        'user_emails_gmail',
        'exclusion_rules',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/gmailscanners/%s/saved/' % self.object.pk


class GmailScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = GmailScanner
    fields = []
    success_url = '/gmailscanners/'


class GmailScannerAskRun(ScannerAskRun):
    """Prompt for starting gmail scan, validate first."""
    model = GmailScanner


class GmailScannerRun(ScannerRun):
    """View that handles starting of a scanner run."""
    model = GmailScanner
