from ..models.scannerjobs.googledrivescanner_model import GoogleDriveScanner
from .scanner_views import *


class GoogleDriveScannerList(ScannerList):
    """Displays a list of file scanners."""
    model = GoogleDriveScanner
    type = 'googledrive'


class GoogleDriveScannerCreate(ScannerCreate):
    """Create a file scanner view"""

    model = GoogleDriveScanner
    fields = [
        'name',
        'schedule',
        'service_account_file',
        'user_emails',
        'exclusion_rules',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/googledrivescanners/%s/created/' % self.object.pk


class GoogleDriveScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = GoogleDriveScanner
    fields = [
        'name',
        'schedule',
        'service_account_file',
        'user_emails',
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
            return '/googledrivescanners/%s/saved/' % self.object.pk


class GoogleDriveScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = GoogleDriveScanner
    fields = []
    success_url = '/googledrivescanners/'


class GoogleDriveScannerAskRun(ScannerAskRun):
    """Prompt for starting google drive scan, validate first."""
    model = GoogleDriveScanner


class GoogleDriveScannerRun(ScannerRun):
    """View that handles starting of a scanner run."""
    model = GoogleDriveScanner
