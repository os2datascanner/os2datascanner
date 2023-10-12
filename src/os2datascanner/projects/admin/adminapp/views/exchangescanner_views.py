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
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework.generics import ListAPIView

from os2datascanner.projects.admin.utilities import UserWrapper
from .scanner_views import (
    ScannerDelete,
    ScannerAskRun,
    ScannerRun,
    ScannerUpdate,
    ScannerCopy,
    ScannerCreate,
    ScannerList,
    ScannerCleanupStaleAccounts)
from ..serializers import OrganizationalUnitSerializer
from ..models.scannerjobs.exchangescanner import ExchangeScanner
from ...core.models import Feature
from ...organizations.models import OrganizationalUnit


class OrganizationalUnitListing(ListAPIView):
    serializer_class = OrganizationalUnitSerializer

    def get_queryset(self):
        organization_id = self.request.query_params.get('organizationId', None)

        if organization_id:
            queryList = OrganizationalUnit.objects.filter(
                    organization=organization_id)
        else:
            queryList = []

        return queryList


class ExchangeScannerList(ScannerList):
    """Displays list of exchange scanners."""

    model = ExchangeScanner
    type = 'exchange'

    def get_queryset(self):
        return super().get_queryset()


class ExchangeScannerBase(View):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = UserWrapper(self.request.user)
        context["org_units"] = (
                OrganizationalUnit.objects.filter(user.make_org_Q()))

        # Needed to upheld feature flags.
        context['FEATURES'] = Feature.__members__
        context['client'] = user.get_client()
        return context


class ExchangeScannerCreate(ExchangeScannerBase, ScannerCreate):
    """Create a exchange scanner view."""

    model = ExchangeScanner
    fields = ['name', 'mail_domain', 'schedule', 'exclusion_rules', 'do_ocr',
              'do_last_modified_check', 'rules', 'userlist', 'only_notify_superadmin',
              'service_endpoint', 'organization', 'org_unit']
    type = 'exchange'

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/exchangescanners/%s/created/' % self.object.pk

    def get_form(self, form_class=None):
        """Adds special field password."""
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        form = initialize_form(form)
        if self.request.method == 'POST':
            form = validate_userlist_or_org_units(form)

        return form


class ExchangeScannerCopy(ExchangeScannerBase, ScannerCopy):
    """Create a new copy of an existing ExchangeScanner"""

    model = ExchangeScanner
    fields = ['name', 'mail_domain', 'schedule', 'exclusion_rules', 'do_ocr',
              'do_last_modified_check', 'rules', 'userlist', 'only_notify_superadmin',
              'service_endpoint', 'organization', 'org_unit']
    type = 'exchange'

    def get_form(self, form_class=None):
        """Adds special field password."""
        # This doesn't copy over it's values, as credentials shouldn't
        # be copyable
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        form = initialize_form(form)
        if self.request.method == 'POST':
            form = validate_userlist_or_org_units(form)

        return form

    def get_initial(self):
        initial = super(ExchangeScannerCopy, self).get_initial()
        initial["userlist"] = self.get_scanner_object().userlist
        return initial


class ExchangeScannerUpdate(ExchangeScannerBase, ScannerUpdate):
    """Update a scanner view."""

    model = ExchangeScanner
    fields = ['name', 'mail_domain', 'schedule', 'exclusion_rules', 'do_ocr',
              'do_last_modified_check', 'rules', 'userlist', 'only_notify_superadmin',
              'service_endpoint', 'organization', 'org_unit']
    type = 'exchange'

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
        if authentication.iv:
            # if there is a set password already, use a dummy to enable the placeholder
            form.fields['password'].initial = "dummy"
        if self.request.method == 'POST':
            form = validate_userlist_or_org_units(form)

        return form


class ExchangeScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = ExchangeScanner
    fields = []
    success_url = '/exchangescanners/'


class ExchangeScannerAskRun(ScannerAskRun):
    """Prompt for starting exchange scan, validate first."""

    model = ExchangeScanner


class ExchangeScannerRun(ScannerRun):
    """View that handles starting of a exchange scanner run."""

    model = ExchangeScanner


def validate_userlist_or_org_units(form):
    """Validates whether the form has either a userlist or organizational units.
    Also checks that the formatting of the userlist is valid.
    NB : must be called after initialize form. """
    form.is_valid()
    if not form.cleaned_data['userlist'] and not form.cleaned_data['org_unit']:
        form.add_error('org_unit', _("No organizational units has been selected"))
        form.add_error('userlist', _("No userlist has been selected"))
    if userlist := form.cleaned_data.get('userlist'):
        users = (u.decode("utf-8").strip() for u in userlist if u.strip())
        for user in users:
            if "@" in user:
                form.add_error(
                    'userlist',
                    _("The userlist should only include the usernames of the "
                      "users, not the domain!"))
                break
            if any(c in user for c in (",", " ")):
                form.add_error(
                    'userlist',
                    _("Usernames in the userlist should be separated by "
                      "newlines, not commas or whitespace!"))
                break
    return form


def initialize_form(form):
    """Initializes the form fields for username and password
    as they are not part of the exchange scanner model."""

    form.fields['mail_domain'].widget.attrs['placeholder'] = _('e.g. @example.com')
    form.fields['username'] = forms.CharField(
        max_length=1024,
        required=False,
        label=_('Username')
    )
    form.fields['password'] = forms.CharField(
        max_length=50,
        required=False,
        label=_('Password')
    )

    return form


class ExchangeCleanupStaleAccounts(ScannerCleanupStaleAccounts):
    """Prompts the user for confirmation before deleting document reports
    belonging to accounts, which have gone stale for this scanner."""
    model = ExchangeScanner
    type = "exchange"
