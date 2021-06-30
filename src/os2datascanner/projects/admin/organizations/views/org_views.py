from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from os2datascanner.projects.admin.core.models import Client, Feature

from ..models import Organization


class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    paginate_by = 10  # TODO: reasonable number? Possibly irrelevant?
    context_object_name = 'client_list'
    template_name = 'organizations/org_list.html'

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
        form.instance.slug = slugify(form.instance.name, allow_unicode=True)
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
