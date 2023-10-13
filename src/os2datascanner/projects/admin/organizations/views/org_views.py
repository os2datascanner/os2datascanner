from typing import Any, Dict
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from os2datascanner.projects.admin.adminapp.views.views import (
    RestrictedDeleteView,
    RestrictedDetailView,
    RestrictedCreateView,
    RestrictedListView,
    RestrictedUpdateView)
from django.core.exceptions import PermissionDenied

from os2datascanner.projects.admin.core.models import Client, Feature, Administrator
from ..models import Organization

import logging

logger = logging.getLogger("admin")


class OrganizationListView(RestrictedListView):
    model = Organization
    paginate_by = 10  # TODO: reasonable number? Possibly irrelevant?
    context_object_name = 'client_list'

    # filter list based on user
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset(org_path="uuid")
        if hasattr(user, 'administrator_for'):
            client_id = user.administrator_for.client_id
            queryset = Client.objects.filter(pk=client_id)
        elif user.is_superuser:
            queryset = Client.objects.all()
        return queryset.prefetch_related('organizations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['FEATURES'] = Feature.__members__
        return context

    def get_template_names(self):
        is_htmx = self.request.headers.get('HX-Request') == "true"
        return 'organizations/org_table.html' if is_htmx else "organizations/org_list.html"


class AddOrganizationView(RestrictedCreateView):
    model = Organization
    template_name = 'organizations/org_add.html'
    success_url = reverse_lazy('organization-list')
    fields = ['name', 'contact_email', 'contact_phone', 'email_notification_schedule']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.required_css_class = 'required-form'
        # form.error_css_class = # TODO: add if relevant?
        return form

    def form_valid(self, form):
        client_id = self.kwargs['client_id']
        form.instance.client = Client.objects.get(pk=client_id)
        if Organization.objects.filter(name=form.instance.name).exists():
            form.add_error('name', _('That name is already taken.'))
            return self.form_invalid(form)
        else:
            return super().form_valid(form)

    def get_queryset(self):
        return super().get_queryset(org_path="uuid")

    def dispatch(self, request, *args, **kwargs):
        client_id = self.kwargs['client_id']
        if request.user.is_superuser or \
                Administrator.objects.filter(user=request.user, client=client_id).exists():
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


class UpdateOrganizationView(RestrictedUpdateView):
    model = Organization
    template_name = 'organizations/org_update.html'
    success_url = reverse_lazy('organization-list')
    fields = ['name', 'contact_email', 'contact_phone',
              'leadertab_access', 'dpotab_access', 'show_support_button',
              'support_contact_method', 'support_name', 'support_value',
              'dpo_contact_method', 'dpo_name', 'dpo_value',
              'email_notification_schedule']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.required_css_class = 'required-form'
        # form.error_css_class = # TODO: add if relevant?
        return form

    def get_queryset(self):
        return super().get_queryset(org_path="uuid")


class DeleteOrganizationView(RestrictedDeleteView):
    """Delete an ogranization view."""
    model = Organization
    success_url = '/organizations/'

    def post(self, request, *args, **kwargs):
        username = request.user.username
        if not User.objects.get(username=username).has_perm("organizations.delete_organization"):
            # Imposter! Keep out!.
            raise PermissionDenied

        # User is OK. Proceed.
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset(org_path="uuid")


class OrganizationDeletionBlocked(RestrictedDetailView):
    """Prompt when user is trying to delete organization with running scannerjob"""
    model = Organization
    fields = []
    template_name = "organizations/org_delete_blocked.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        return super().get_context_data(**kwargs)
