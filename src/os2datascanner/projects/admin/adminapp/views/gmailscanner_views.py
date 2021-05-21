# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
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
        'organization',
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
        'organization',
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
