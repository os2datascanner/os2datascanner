from django import forms

from .scanner_views import *
from ..aescipher import decrypt
from ..models.scannerjobs.exchangescanner_model import ExchangeScanner


class ExchangeScannerList(ScannerList):
    """Displays list of exchange scanners."""

    model = ExchangeScanner
    type = 'exchange'


class ExchangeScannerCreate(ScannerCreate):
    """Create a exchange scanner view."""

    model = ExchangeScanner
    fields = ['name', 'url', 'schedule', 'exclusion_rules', 'do_ocr',
              'do_last_modified_check', 'rules', 'recipients', 'userlist',
              'service_endpoint']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/exchangescanners/%s/created/' % self.object.pk

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        return initialize_form(form)


class ExchangeScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = ExchangeScanner
    fields = ['name', 'url', 'schedule', 'exclusion_rules', 'do_ocr',
              'do_last_modified_check', 'rules', 'recipients', 'userlist',
              'service_endpoint']

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/exchangescanners/%s/saved/' % self.object.pk

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form = initialize_form(form)

        exchangescanner = self.get_object()
        authentication = exchangescanner.authentication

        if authentication.username:
            form.fields['username'].initial = authentication.username
        if authentication.ciphertext:
            password = decrypt(bytes(authentication.iv),
                               bytes(authentication.ciphertext))
            form.fields['password'].initial = password

        return form


class ExchangeScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = ExchangeScanner
    fields = []
    success_url = '/exchangescanners/'


class ExchangeScannerAskRun(ScannerAskRun):
    """Prompt for starting exchange scan, validate first."""

    model = ExchangeScanner

    def get_context_data(self, **kwargs):
        """Check that user is allowed to run this scanner."""
        context = super().get_context_data(**kwargs)
        context['ok'] = True
        return context


class ExchangeScannerRun(ScannerRun):
    """View that handles starting of a exchange scanner run."""

    model = ExchangeScanner


def initialize_form(form):
    """Initializes the form fields for username and password
    as they are not part of the exchange scanner model."""

    form.fields['username'] = forms.CharField(max_length=1024, required=False, label='Brugernavn')
    form.fields['password'] = forms.CharField(max_length=50, required=False)

    return form
