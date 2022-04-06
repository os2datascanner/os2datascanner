"""
Views for adding and updating configurations for Microsoft Graph
for importing organizations.
"""
from urllib.parse import urlencode
from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView

from os2datascanner.projects.admin.organizations.models import Organization
from ..models.msgraph_configuration import MSGraphConfiguration
from os2datascanner.projects.admin.import_services.utils import start_msgraph_import


def make_consent_url(label):
    """
    Directs the user to Microsoft Online in order to obtain consent.
    After successful login to Microsoft Online, the user is redirected to
    'organizations'.
    """
    if settings.MSGRAPH_APP_ID:
        redirect_uri = settings.SITE_URL + "{0}".format(label)
        return ("https://login.microsoftonline.com/common/adminconsent?"
                + urlencode({
                    "client_id": settings.MSGRAPH_APP_ID,
                    "scope": "https://graph.microsoft.com/.default",
                    "response_type": "code",
                    "redirect_uri": redirect_uri
                }))
    return None


class MSGraphEditForm(forms.ModelForm):
    required_css_class = 'required-form'

    class Meta:
        model = MSGraphConfiguration
        fields = [
            'tenant_id',
        ]


class MSGraphAddView(View):
    """
    View for adding a configuration for Microsoft Graph to import an organization.
    Works as a dispatcher depending on whether or not the user is logged into
    Microsoft Online.
    """
    model = MSGraphConfiguration
    type = "msgraph-add"

    def dispatch(self, request, *args, **kwargs):
        tenant_id = None
        if "tenant_id" in kwargs:
            tenant_id = kwargs["tenant_id"]
        org_id = kwargs["org_id"]

        if tenant_id and org_id:
            handler = _MSGraphAddView.as_view()
        else:
            handler = _MSGraphPermissionRequest.as_view()
        return handler(request, *args, **kwargs)


class _MSGraphAddView(LoginRequiredMixin, CreateView):
    """
    View for adding a configuration for importing organizations through
    Microsoft Graph by using a Tenant ID.
    """

    model = MSGraphConfiguration
    template_name = 'import_services/msgraph_edit.html'
    success_url = reverse_lazy('organization-list')
    form_class = MSGraphEditForm

    def setup(self, request, *args, **kwargs):
        organization = get_object_or_404(Organization, pk=kwargs['org_id'])
        kwargs["organization"] = organization
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = True
        context["tenant_id"] = self.kwargs["tenant_id"]
        context["organization"] = self.kwargs["organization"]
        return context

    def form_valid(self, form):
        form.instance.created = now()
        form.instance.last_modified = now()
        form.instance.tenant_id = self.kwargs["tenant_id"]
        form.instance.organization = self.kwargs['organization']
        result = super().form_valid(form)
        return result


class _MSGraphPermissionRequest(LoginRequiredMixin, TemplateView):
    """
    Landing page for users who have not been authenticated through Microsoft
    Online.
    """

    template_name = "import_services/msgraph_oauth.html"

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            **{
                "service_name": "Microsoft Online",
                "auth_endpoint": make_consent_url("organizations"),
                "error": self.request.GET.get("error"),
                "error_description": self.request.GET.get("error_description"),
            }
        )


class MSGraphUpdateView(LoginRequiredMixin, UpdateView):
    """
    Page where the user can edit the configuration for Microsoft Graph
    for importing organizations.
    """

    model = MSGraphConfiguration
    template_name = 'import_services/msgraph_edit.html'
    success_url = reverse_lazy('organization-list')
    form_class = MSGraphEditForm

    def setup(self, request, *args, **kwargs):
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = False
        context['tenant_id'] = self.kwargs['tenant_id']
        context['organization'] = self.object.organization
        return context

    def form_valid(self, form):
        form.instance.last_modified = now()
        form.instance.tenant_id = self.kwargs["tenant_id"]
        form.instance.organization = self.kwargs['organization']
        return super().form_valid(form)


class MSGraphImportView(LoginRequiredMixin, DetailView):
    """
    """

    model = MSGraphConfiguration

    def __init__(self):
        self.object = None

    def get(self, request, *args, **kwargs):
        """
        """
        start_msgraph_import(self.get_object())

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
