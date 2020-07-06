from django import forms
from .scanner_views import *
from ..aescipher import decrypt
from ..models.scannerjobs.dropboxscanner_model import DropboxScanner


class DropboxScannerList(ScannerList):
    """Displays list of file scanners."""

    model = DropboxScanner
    type = 'dropbox'


class DropboxScannerCreate(ScannerCreate):
    """Create a file scanner view."""

    model = DropboxScanner
    fields = [
        'name',
        'schedule',
        'exclusion_rules',
        'token',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/dropboxscanners/%s/created/' % self.object.pk


class DropboxScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = DropboxScanner
    fields = [
        'name',
        'schedule',
        'exclusion_rules',
        'token',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'recipients'
    ]

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        return form

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/dropboxscanners/%s/saved/' % self.object.pk


class DropboxScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = DropboxScanner
    fields = []
    success_url = '/dropboxscanners/'


class DropboxScannerAskRun(ScannerAskRun):
    """Prompt for starting dropbox scan, validate first."""

    model = DropboxScanner


class DropboxScannerRun(ScannerRun):
    """View that handles starting of a file scanner run."""

    model = DropboxScanner
