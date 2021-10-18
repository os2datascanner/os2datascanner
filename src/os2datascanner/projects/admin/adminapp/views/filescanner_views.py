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
from django import forms
from .scanner_views import (
    ScannerDelete,
    ScannerAskRun,
    ScannerRun,
    ScannerUpdate,
    ScannerCopy,
    ScannerCreate,
    ScannerList)
from ..aescipher import decrypt
from ..models.scannerjobs.filescanner_model import FileScanner
from django.utils.translation import ugettext_lazy as _


class FileScannerList(ScannerList):
    """Displays list of file scanners."""

    model = FileScanner
    type = 'file'


class FileScannerCreate(ScannerCreate):
    """Create a file scanner view."""

    model = FileScanner
    type = 'file'
    fields = [
        'name',
        'schedule',
        'url',
        'exclusion_rules',
        'alias',
        'do_ocr',
        'do_last_modified_check',
        'skip_super_hidden',
        'rules',
        'organization',
        ]

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        return initialize_form(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filescanners/%s/created/' % self.object.pk


class FileScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = FileScanner
    type = 'file'
    fields = [
        'name',
        'schedule',
        'url',
        'exclusion_rules',
        'alias',
        'do_ocr',
        'do_last_modified_check',
        'skip_super_hidden',
        'rules',
        'organization',
        ]

    def get_form(self, form_class=None):
        """Adds special field password and decrypts password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        form = initialize_form(form)

        filedomain = self.get_object()
        authentication = filedomain.authentication

        if authentication.username:
            form.fields['username'].initial = authentication.username
        if authentication.ciphertext:
            password = decrypt(bytes(authentication.iv),
                               bytes(authentication.ciphertext))
            form.fields['password'].initial = password
        if authentication.domain:
            form.fields['domain'].initial = authentication.domain

        return form

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/filescanners/%s/saved/' % self.object.pk


class FileScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = FileScanner
    fields = []
    success_url = '/filescanners/'


class FileScannerCopy(ScannerCopy):
    """Create a new copy of an existing FileScanner"""
    model = FileScanner
    type = 'file'
    fields = [
        'name',
        'schedule',
        'url',
        'exclusion_rules',
        'alias',
        'do_ocr',
        'do_last_modified_check',
        'rules',
        'organization',
        ]

    def get_form(self, form_class=None):
        """Adds special field password."""
        # This doesn't copy over it's values, as credentials shouldn't
        # be copyable
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        return initialize_form(form)


class FileScannerAskRun(ScannerAskRun):
    """Prompt for starting file scan, validate first."""

    model = FileScanner


class FileScannerRun(ScannerRun):
    """View that handles starting of a file scanner run."""

    model = FileScanner


def initialize_form(form):
    """Initializes the form fields for username and password
    as they are not part of the file scanner model."""

    form.fields['url'].widget.attrs['placeholder'] = _('e.g. //network-domain/top-folder')
    form.fields['username'] = forms.CharField(max_length=1024, required=False, label=_('Username'))
    form.fields['password'] = forms.CharField(max_length=50, required=False, label=_('Password'))
    form.fields['domain'] = forms.CharField(max_length=2024, required=False, label=_('User domain'))
    form.fields['alias'] = forms.CharField(max_length=64, required=False, label=_('Drive letter'))

    return form
