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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Contains Django views."""

import codecs
import os
import tempfile
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import View, ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.edit import ModelFormMixin, DeleteView
from shutil import copyfile

from ..forms import FileUploadForm
from ..models.scannerjobs.exchangescanner_model import ExchangeScanner
from ..models.scannerjobs.filescanner_model import FileScanner
from ..models.group_model import Group
from ..models.organization_model import Organization
from ..models.rules.cprrule_model import CPRRule
from ..models.rules.regexrule_model import RegexRule
from ..models.userprofile_model import UserProfile
from ..models.scannerjobs.webscanner_model import WebScanner
from ..utils import do_scan, as_file_uri


class LoginRequiredMixin(View):
    """Include to require login.

    If user is "upload only", redirect to upload page."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """Check for login and dispatch the view."""
        user = self.request.user
        try:
            profile = user.profile
            if profile.is_upload_only:
                return redirect('system/upload_file')
        except UserProfile.DoesNotExist:
            # User is *not* "upload only", all is good
            pass
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
        if user.is_superuser:
            return self.model.objects.all()
        else:
            try:
                profile = user.profile
                if profile.organization.do_use_groups:
                    if profile.is_group_admin or self.model == Group:
                        return self.model.objects.filter(
                            organization=profile.organization
                        )
                    else:
                        groups = profile.groups.all()
                        qs = self.model.objects.filter(
                            organization=profile.organization
                        ).filter(
                            Q(group__in=groups) | Q(group__isnull=True)
                        )
                        return qs
                else:
                    return self.model.objects.filter(
                        organization=profile.organization
                    )

            except UserProfile.DoesNotExist:
                return self.model.objects.filter(organization=None)


class MainPageView(TemplateView, LoginRequiredMixin):
    """Display the main page."""

    template_name = 'os2datascanner/scanners.html'

class DesignGuide(TemplateView):
    template_name = 'designguide.html'

class OrganizationList(RestrictedListView):
    """Display a list of organizations, superusers only!"""

    model = Organization
    template_name = 'os2datascanner/organizations_and_domains.html'

    def get_context_data(self, **kwargs):
        """Setup context for the template."""
        context = super().get_context_data(**kwargs)
        organization_list = context['organization_list']
        orgs_with_domains = []
        for org in organization_list:
            tld_list = []

            def top_level(d):
                return '.'.join(d.strip('/').split('.')[-2:])

            tlds = set([top_level(d.url) for d in
                        org.scanner_set.all()])

            for tld in tlds:
                sub_domains = [
                    d.url for d in org.scanner_set.all() if top_level(d.url) ==
                                                         tld
                ]
                tld_list.append({'tld': tld, 'domains': sub_domains})

            orgs_with_domains.append({'name': org.name, 'domains': tld_list})

        context['orgs_with_domains'] = orgs_with_domains

        return context


class GroupList(RestrictedListView):
    """Displays groups for organization."""

    model = Group
    template_name = 'os2datascanner/groups.html'


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

        if user.is_superuser:
            fields.append('organization')
        elif user.profile.organization.do_use_groups:
            if (
                user.profile.is_group_admin or
                len(user.profile.groups.all()) > 1
            ):
                fields.append('group')

        return fields

    def get_form(self, form_class=None):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()

        form = form_class(**kwargs)
        user = self.request.user

        if 'group' in fields:
            if user.profile.is_group_admin:
                queryset = (
                    user.profile.organization.groups.all()
                )
            else:
                form.fields['group'].queryset = (
                    user.profile.groups.all()
                )
            form.fields['group'].queryset = queryset
        return form

    def form_valid(self, form):
        """Validate the form."""
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.profile
            except UserProfile.DoesNotExist:
                raise PermissionDenied
            self.object = form.save(commit=False)
            self.object.organization = user_profile.organization
            if (
                    user_profile.organization.do_use_groups and not
            user_profile.is_group_admin and
                    len(user_profile.groups.all())
            ):
                self.object.group = user_profile.groups.all()[0]

        return super().form_valid(form)


class OrgRestrictedMixin(ModelFormMixin, LoginRequiredMixin):
    """Mixin class for views with organization-restricted queryset."""

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        if not self.fields:
            return []
        fields = [f for f in self.fields]
        user = self.request.user
        organization = self.object.organization
        do_add_group = False
        if user.is_superuser:
            fields.append('organization')
        if organization.do_use_groups:
            if (
                    user.is_superuser or
                    user.profile.is_group_admin or
                    len(user.profile.groups.all()) > 1
            ):
                do_add_group = True
        if do_add_group and self.model != Group:
            fields.append('group')
        return fields

    def get_form(self, form_class=None):
        """Get the form for the view."""
        fields = self.get_form_fields()
        form_class = modelform_factory(self.model, fields=fields)
        kwargs = self.get_form_kwargs()

        form = form_class(**kwargs)
        user = self.request.user

        if 'group' in fields:
            if user.is_superuser or user.profile.is_group_admin:
                form.fields['group'].queryset = (
                    self.object.organization.groups.all()
                )
            else:
                form.fields['group'].queryset = (
                    user.profile.groups.all()
                )
        return form

    def get_queryset(self):
        """Get queryset filtered by user's organization."""
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            organization = None

            try:
                user_profile = self.request.user.profile
                organization = user_profile.organization
                groups = user_profile.groups.all()
            except UserProfile.DoesNotExist:
                organization = None
                groups = []

            if (
                    user_profile.organization.do_use_groups and not
            user_profile.is_group_admin
            ):
                queryset = queryset.filter(
                    Q(group__in=groups) | Q(group__isnull=True)
                )
            else:
                queryset = queryset.filter(organization=organization)
        return queryset


class RestrictedUpdateView(UpdateView, OrgRestrictedMixin):
    """Base class for updateviews restricted by organiztion."""



class RestrictedDetailView(DetailView, OrgRestrictedMixin):
    """Base class for detailviews restricted by organiztion."""



class RestrictedDeleteView(DeleteView, OrgRestrictedMixin):
    """Base class for deleteviews restricted by organiztion."""


class GroupCreate(RestrictedCreateView):
    """Create a group view."""

    fields = ['name', 'contact_email', 'contact_phone', 'user_profiles']
    model = Group

    def get_form_fields(self):
        """Get the list of fields to use in the form for the view."""
        fields = super().get_form_fields()

        if 'group' in fields:
            fields.remove('group')

        return fields

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)

        field_name = 'user_profiles'
        queryset = form.fields[field_name].queryset
        queryset = queryset.filter(organization=0)
        form.fields[field_name].queryset = queryset

        return form

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/groups/%s/created/' % self.object.pk


class GroupUpdate(RestrictedUpdateView):
    """Update a domain view."""

    model = Group
    fields = ['name', 'contact_email', 'contact_phone', 'user_profiles']

    def get_form(self, form_class=None):
        """Get the form for the view.

        Querysets used for choices in the 'domains' and 'rules' fields
        will be limited by the user's organiztion unless the user is a
        superuser.
        """
        if form_class is None:
            form_class = self.get_form_class()

        form = super().get_form(form_class)
        group = self.get_object()
        field_name = 'user_profiles'
        queryset = form.fields[field_name].queryset
        if group.organization:
            queryset = queryset.filter(organization=group.organization)
        else:
            queryset = queryset.filter(organization=0)
        form.fields[field_name].queryset = queryset
        return form

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/groups/%s/saved/' % self.object.pk


class GroupDelete(RestrictedDeleteView):
    """Delete a domain view."""

    model = Group
    fields = ['name', 'contact_email', 'contact_phone', 'user_profiles']
    success_url = '/groups/'


class DialogSuccess(TemplateView):
    """View that handles success for iframe-based dialogs."""

    template_name = 'os2datascanner/dialogsuccess.html'

    type_map = {
        'webscanners': WebScanner,
        'filescanners': FileScanner,
        'exchangescanners': ExchangeScanner,
        'rules/cpr': CPRRule,
        'rules/regex': RegexRule,
        'groups': Group
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
        context['action'] = "oprettet" if created else "gemt"
        if model_type in self.reload_map:
            model_type = self.reload_map[model_type]
        context['reload_url'] = '/' + model_type + '/'
        return context
