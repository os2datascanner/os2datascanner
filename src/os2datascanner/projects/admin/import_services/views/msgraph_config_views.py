"""
Views for adding and updating configurations for Microsoft Graph
for importing organizations.
"""

from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.detail import DetailView

from ..models.msgraph_configuration import MSGraphConfig


def make_consent_url(label):
    """
    Directs the user to Microsoft Online in order to obtain consent.
    After successful login to Microsoft Online, the user is redirected to
    'imports/msgraph-<label>/add/'.
    """
    if settings.MSGRAPH_APP_ID:
        redirect_uri = settings.SITE_URL + "imports/msgraph-{0}/add/".format(label)
        return ("https://login.microsoftonline.com/common/adminconsent?"
                + urlencode({
                    "client_id": settings.MSGRAPH_APP_ID,
                    "scope": "https://graph.microsoft.com/.default",
                    "response_type": "code",
                    "redirect_uri": redirect_uri
                }))
    return None


class MSGraphAddView(View):
    """
    View for adding a configuration for Microsoft Graph to import an organization.
    Works as a dispatcher depending on whether or not the user is logged into
    Microsoft Online.
    """

    type = "msgraph-add"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            if "tenant" in request.POST:
                tenant_id = request.POST.get('tenant')
                # TODO: Run an msgraph_import_job here!
                return HttpResponseRedirect(reverse_lazy('organization-list'))

            raise Http404("No tenant id available.")

        if "tenant" in request.GET:
            handler = _MSGraphAddView.as_view()
        else:
            handler = _MSGraphPermissionRequest.as_view()
        return handler(request, *args, **kwargs)


class _MSGraphAddView(LoginRequiredMixin, CreateView):
    """
    View for adding a configuration for importing organizations through
    Microsoft Graph by using a Tenant ID.
    """

    model = MSGraphConfig
    template_name = 'import_services/msgraph_edit.html'
    success_url = reverse_lazy('organization-list')
    fields = ['tenant']

    def setup(self, request, *args, **kwargs):
        tenant_id = request.GET.get("tenant")
        kwargs["tenant"] = tenant_id
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tenant"] = self.kwargs["tenant"]
        return context

    def form_valid(self, form):
        form.instance.created = now()
        form.instance.last_modified = now()
        form.instance.tenant = self.kwargs["tenant"]
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
                "auth_endpoint": make_consent_url("organization"),
                "error": self.request.GET.get("error"),
                "error_description": self.request.GET.get("error_description"),
            }
        )


class MSGraphUpdateView(LoginRequiredMixin, UpdateView):
    """
    Page where the user can edit the configuration for Microsoft Graph
    for importing organizations.
    """

    model = MSGraphConfig
    template_name = 'import_services/msgraph_edit.html'
    success_url = reverse_lazy('organization-list')
    fields = ['tenant']

    def setup(self, request, *args, **kwargs):
        tenant_id = request.GET.get("tenant")
        kwargs["tenant"] = tenant_id
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.kwargs['tenant']
        return context

    def form_valid(self, form):
        form.instance.tenant = self.kwargs["tenant"]
        return super().form_valid(form)


class MSGraphImportView(LoginRequiredMixin, DetailView):
    """
    """

    model = MSGraphConfig

    def __init__(self):
        self.object = None

    def get(self, request, *args, **kwargs):
        """
        """

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
