from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _

from os2datascanner.projects.admin.core.models import Client, Feature
from ..models import Organization

import logging

logger = logging.getLogger("admin")

# Codes sourced from https://www.thesauruslex.com/typo/eng/enghtml.htm
char_dict = {
        "Æ": "&AElig;",
        "Ø": "&Oslash;",
        "Å": "&Aring;",
        "æ": "&aelig;",
        "ø": "&oslash;",
        "å": "&aring;",
        }


def replace_nordics(name: str):
    """ Replaces 'æ', 'ø' and 'å' with 'ae', 'oe' and 'aa'. """
    global char_dict
    for char in char_dict:
        name = name.replace(char, char_dict[char])
    return name


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    paginate_by = 10  # TODO: reasonable number? Possibly irrelevant?
    context_object_name = 'client_list'
    template_name = 'organizations/org_list.html'

    def setup(self, request, *args, **kwargs):
        tenant_id = request.GET.get("tenant")
        kwargs["tenant_id"] = tenant_id
        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if request.GET.get('tenant'):
            tenant_id = request.GET.get('tenant')
            org_id = request.GET.get('state')
            return redirect('add-msgraph',
                            org_id=org_id,
                            tenant_id=tenant_id)
        return super(OrganizationListView, self).get(request, *args, **kwargs)

    # filter list based on user
    def get_queryset(self):
        user = self.request.user
        queryset = Organization.objects.none()
        if hasattr(user, 'administrator_for'):
            client_id = user.administrator_for.client_id
            queryset = Client.objects.filter(pk=client_id)
        elif user.is_superuser:
            queryset = Client.objects.all()
        return queryset.prefetch_related('organizations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['FEATURES'] = Feature.__members__
        context["tenant_id"] = self.kwargs["tenant_id"]
        return context


class AddOrganizationView(LoginRequiredMixin, CreateView):
    model = Organization
    template_name = 'organizations/org_add.html'
    success_url = reverse_lazy('organization-list')
    fields = ['name', 'contact_email', 'contact_phone']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.required_css_class = 'required-form'
        # form.error_css_class = # TODO: add if relevant?
        return form

    def form_valid(self, form):
        client_id = self.kwargs['client_id']
        form.instance.client = Client.objects.get(pk=client_id)
        encoded_name = replace_nordics(form.instance.name)
        form.instance.slug = slugify(encoded_name, allow_unicode=True)
        if Organization.objects.filter(slug=form.instance.slug).exists():
            form.add_error('name', _('That name is already taken.'))
            return self.form_invalid(form)
        else:
            return super().form_valid(form)


class UpdateOrganizationView(LoginRequiredMixin, UpdateView):
    model = Organization
    template_name = 'organizations/org_update.html'
    success_url = reverse_lazy('organization-list')
    fields = ['name', 'contact_email', 'contact_phone']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.required_css_class = 'required-form'
        # form.error_css_class = # TODO: add if relevant?
        return form
