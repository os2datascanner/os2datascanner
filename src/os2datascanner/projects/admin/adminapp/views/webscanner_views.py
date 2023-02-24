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
from os2datascanner.projects.admin.adminapp.views.views import RestrictedDetailView
from ..validate import validate_domain, get_validation_str
from .scanner_views import (
    ScannerDelete,
    ScannerAskRun,
    ScannerRun,
    ScannerUpdate,
    ScannerCopy,
    ScannerCreate,
    ScannerList)
from ..models.scannerjobs.webscanner import WebScanner
from django.utils.translation import ugettext_lazy as _


def url_contains_spaces(form):
    return form['url'].value() and ' ' in form['url'].value()


class WebScannerList(ScannerList):
    """Displays list of web scanners."""

    model = WebScanner
    type = 'web'


class WebScannerCreate(ScannerCreate):
    """Web scanner create form."""

    model = WebScanner
    type = 'web'
    fields = ['name', 'schedule', 'url', 'exclusion_rules',
              'download_sitemap', 'sitemap_url', 'sitemap', 'do_ocr',
              'do_link_check', 'only_notify_superadmin', 'do_last_modified_check',
              'rules', 'organization', 'exclude_urls', 'reduce_communication']

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        form.fields['url'].widget.attrs['placeholder'] = \
            _('e.g. https://example.com')
        form.fields['exclude_urls'].widget.attrs['placeholder'] = \
            _('e.g. https://example.com/exclude1, https://example.com/exclude2')

        return form

    def form_valid(self, form):
        if url_contains_spaces(form):
            form.add_error('url', _(u'Space is not allowed in the web-domain name.'))
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/webscanners/%s/created/' % self.object.pk


class WebScannerCopy(ScannerCopy):
    """Create a new copy of an existing WebScanner"""

    model = WebScanner
    type = 'web'
    fields = ['name', 'schedule', 'url', 'exclusion_rules',
              'download_sitemap', 'sitemap_url', 'sitemap', 'do_ocr',
              'do_link_check', 'only_notify_superadmin', 'do_last_modified_check',
              'rules', 'organization', 'exclude_urls', 'reduce_communication']


class WebScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = WebScanner
    type = 'web'
    fields = ['name', 'schedule', 'url', 'exclusion_rules',
              'download_sitemap', 'sitemap_url', 'sitemap', 'do_ocr',
              'do_link_check', 'only_notify_superadmin', 'do_last_modified_check',
              'rules', 'organization', 'exclude_urls', 'reduce_communication']

    def form_valid(self, form):
        if url_contains_spaces(form):
            form.add_error('url', _(u'Space is not allowed in the web-domain name.'))
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Get the context used when rendering the template."""
        context = super().get_context_data(**kwargs)
        for value, _desc in WebScanner.validation_method_choices:
            key = 'valid_txt_' + str(value)
            context[key] = get_validation_str(self.object, value)
        return context

    def get_success_url(self):
        """The URL to redirect to after successful updating.

        Will redirect the user to the validate view if the form was submitted
        with the 'save_and_validate' button.
        """
        if 'save_and_validate' in self.request.POST:
            return 'validate/'
        else:
            return '/webscanners/%s/saved/' % self.object.pk


class WebScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = WebScanner
    fields = []
    success_url = '/webscanners/'


class WebScannerAskRun(ScannerAskRun):
    """Prompt for starting web scan, validate first."""

    model = WebScanner


class WebScannerRun(ScannerRun):
    """View that handles starting of a web scanner run."""

    model = WebScanner


class WebScannerValidate(RestrictedDetailView):
    """View that handles validation of a domain."""

    model = WebScanner

    def get_context_data(self, **kwargs):
        """Perform validation and populate the template context."""
        context = super().get_context_data(**kwargs)
        context['validation_status'] = self.object.validation_status
        if not self.object.validation_status:
            result = validate_domain(self.object)

            if result:
                self.object.validation_status = self.model.VALID
                self.object.save()

            context['validation_success'] = result

        return context
