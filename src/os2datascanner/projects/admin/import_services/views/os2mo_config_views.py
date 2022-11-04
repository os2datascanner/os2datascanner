"""
Views for adding and updating configurations for OS2mo
for importing organizations.
"""

from django import forms
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView

from os2datascanner.projects.admin.organizations.models import Organization
from ..models.os2mo_configuration import OS2moConfiguration
from os2datascanner.projects.admin.import_services.utils import start_os2mo_import


class OS2moEditForm(forms.ModelForm):
    required_css_class = 'required-form'

    def __init__(self, *args, **kwargs):
        super(OS2moEditForm, self).__init__(*args, **kwargs)
        self.fields['organization'].disabled = True

    class Meta:
        model = OS2moConfiguration
        fields = [
            'organization',
        ]

    organization = forms.CharField()


class OS2moAddView(View):
    """
    View for adding a configuration for OS2mo to import an organization.
    The user is required to have both a OS2mo Client ID- and Secret.
    """
    model = OS2moConfiguration
    type = "os2mo-add"

    def dispatch(self, request, *args, **kwargs):
        if settings.OS2MO_CLIENT_ID and settings.OS2MO_CLIENT_SECRET:
            handler = _OS2moAddView.as_view()
        else:
            handler = _OS2moErrorView.as_view(
                    redirect_token="add-os2mo",
                    redirect_kwargs=dict(org_id=str(kwargs["org_id"])))
        return handler(request, *args, **kwargs)


class _OS2moAddView(LoginRequiredMixin, CreateView):
    """
    View for adding a configuration for importing organizations through
    OS2mo. Only needs organization uuid.
    """
    template_name = 'import_services/os2mo_edit.html'
    success_url = reverse_lazy('organization-list')
    form_class = OS2moEditForm

    def setup(self, request, *args, **kwargs):
        org = get_object_or_404(Organization, pk=kwargs['org_id'])
        self.initial = {
            "organization": org.pk,
        }
        kwargs["organization"] = org
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = True
        context["organization"] = self.kwargs["organization"]
        return context

    def form_valid(self, form):
        form.instance.created = now()
        form.instance.last_modified = now()
        form.instance.organization = self.kwargs['organization']
        result = super().form_valid(form)
        return result


class _OS2moErrorView(LoginRequiredMixin, TemplateView):
    """
    Landing page for users who do have a OS2mo Client ID- and Secret
    """
    template_name = "import_services/os2mo_errorview.html"

    redirect_token = None
    redirect_kwargs = None


class OS2moImportView(LoginRequiredMixin, DetailView):
    """
    View for creating background import jobs with OS2mo.
    """

    model = OS2moConfiguration

    def __init__(self):
        self.object = None

    def get(self, request, *args, **kwargs):
        """
        Initiates importation of an organization through OS2mo.
        """
        start_os2mo_import(self.get_object())

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
