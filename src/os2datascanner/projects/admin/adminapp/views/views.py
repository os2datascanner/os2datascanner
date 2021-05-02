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
"""Contains Django views."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.edit import ModelFormMixin, DeleteView

from ..models.scannerjobs.dropboxscanner_model import DropboxScanner
from ..models.scannerjobs.exchangescanner_model import ExchangeScanner
from ..models.scannerjobs.filescanner_model import FileScanner
from ..models.scannerjobs.gmail_model import GmailScanner
from ..models.scannerjobs.sbsysscanner_model import SbsysScanner
from ..models.rules.cprrule_model import CPRRule
from ..models.rules.regexrule_model import RegexRule
from ..models.scannerjobs.msgraph_models import (
        MSGraphFileScanner, MSGraphMailScanner)
from ..models.scannerjobs.webscanner_model import WebScanner
from ..models.scannerjobs.googledrivescanner_model import GoogleDriveScanner


class LoginRequiredMixin(View):
    """Include to require login."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
        return super().dispatch(*args, **kwargs)


class SuperUserRequiredMixin(LoginRequiredMixin):
    """Include to require login and superuser."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and superuser and dispatch the view."""
        user = self.request.user
        if user.is_superuser:
            return super().dispatch(*args, **kwargs)
        else:
            raise PermissionDenied


class RestrictedListView(ListView, LoginRequiredMixin):
    """Make sure users only see data that belong to their own organization."""

    def get_queryset(self):
        """Restrict to the organization of the logged-in user."""
        user = self.request.user
        if user.is_superuser and user.is_active:
            return self.model.objects.all()
        else:
            return self.model.objects.none()


class MainPageView(TemplateView, LoginRequiredMixin):
    """Display the main page."""

    template_name = 'os2datascanner/scanners.html'


class DesignGuide(TemplateView):
    template_name = 'designguide.html'


class RuleList(RestrictedListView):
    """Displays list of scanners."""

    model = RegexRule
    template_name = 'os2datascanner/rules.html'


# Create/Update/Delete Views.

class RestrictedCreateView(CreateView, LoginRequiredMixin):
    """Base class for create views that are limited by user organization."""

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        fields = [f for f in self.fields]
        user = self.request.user
        if user.is_superuser or user.is_staff:
            fields.append('organization')

        return fields

    def get_form(self, form_class=None):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()
        form = form_class(**kwargs)

        return form

    def form_valid(self, form):
        """Validate the form."""
        user = self.request.user
        if not user.is_superuser or not user.is_staff:
            self.object = form.save(commit=False)

        return super().form_valid(form)


class OrgRestrictedMixin(ModelFormMixin, LoginRequiredMixin):
    """Mixin class for views with organization-restricted queryset."""

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        if not self.fields:
            return []
        fields = [f for f in self.fields]
        user = self.request.user
        if user.is_superuser or user.is_staff:
            fields.append('organization')

        return fields

    def get_form(self, form_class=None):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()
        form = form_class(**kwargs)

        return form

    def get_queryset(self):
        """Get queryset filtered by user's organization."""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser or not user.is_staff:
            queryset = queryset.filter(
                ldap_organization__in=user.administrator_for.client.organizations.all()
            )
        return queryset


class RestrictedUpdateView(UpdateView, OrgRestrictedMixin):
    """Base class for updateviews restricted by organiztion."""


class RestrictedDetailView(DetailView, OrgRestrictedMixin):
    """Base class for detailviews restricted by organiztion."""


class RestrictedDeleteView(DeleteView, OrgRestrictedMixin):
    """Base class for deleteviews restricted by organiztion."""


class DialogSuccess(TemplateView):
    """View that handles success for iframe-based dialogs."""

    template_name = 'os2datascanner/dialogsuccess.html'

    type_map = {
        'webscanners': WebScanner,
        'filescanners': FileScanner,
        'exchangescanners': ExchangeScanner,
        'dropboxscanners': DropboxScanner,
        'msgraph-filescanners': MSGraphFileScanner,
        'msgraph-mailscanners': MSGraphMailScanner,
        'googledrivescanners' : GoogleDriveScanner,
        'gmailscanners': GmailScanner,
        'sbsysscanners': SbsysScanner,
        'rules/cpr': CPRRule,
        'rules/regex': RegexRule,
    }

    reload_map = {
        'rules/cpr': 'rules',
        'rules/regex': 'rules'
    }

    def get_context_data(self, **kwargs):
        """Setup context for the template."""
        context = super().get_context_data(**kwargs)
        model_type = self.args[0]
        pk = self.args[1]
        created = self.args[2] == 'created'
        if model_type not in self.type_map:
            raise Http404
        model = self.type_map[model_type]
        item = get_object_or_404(model, pk=pk)
        context['item_description'] = item.display_name
        context['action'] = _("created") if created else _("saved")
        if model_type in self.reload_map:
            model_type = self.reload_map[model_type]
        context['reload_url'] = '/' + model_type + '/'
        return context
