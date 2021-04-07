from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic.edit import CreateView, UpdateView

from os2datascanner.projects.admin.import_services.keycloak_services import add_or_update_ldap_conf
from os2datascanner.projects.admin.organizations.models import Organization

from os2datascanner.projects.admin.import_services.models import LDAPConfig, Realm


class LDAPEditForm(forms.ModelForm):
    """TODO:"""
    required_css_class = 'required-form'

    class Meta:
        model = LDAPConfig
        fields = [  # Specify default order of form fields:
            'connection_protocol',
            'connection_url',
            'bind_dn',
            'ldap_password',
            'vendor',
            'username_attribute',
            'rdn_attribute',
            'uuid_attribute',
            'users_dn',
            'search_scope',
            'user_obj_classes',
        ]
        widgets = {
            'bind_dn': forms.TextInput(),
            'users_dn': forms.TextInput(),
            'user_obj_classes': forms.TextInput(),
        }

    ldap_password = forms.CharField(
        widget=forms.PasswordInput(),
        help_text="",  # TODO: add text
        # TODO: add translated label
    )

    @staticmethod
    def connection_fields():
        fields = [
            'bind_dn',
            'ldap_password',
        ]
        return fields

    @staticmethod
    def general_fields():
        fields = [
            'vendor',
        ]
        return fields

    @staticmethod
    def user_location_fields():
        fields = [
            'users_dn',
            'search_scope',
            'user_obj_classes',
        ]
        return fields

    @staticmethod
    def user_attribute_fields():
        fields = [
            'username_attribute',
            'rdn_attribute',
            'uuid_attribute',
        ]
        return fields


class LDAPAddView(LoginRequiredMixin, CreateView):
    model = LDAPConfig
    template_name = 'import_services/ldap_edit.html'
    success_url = reverse_lazy('organization-list')
    form_class = LDAPEditForm

    def setup(self, request, *args, **kwargs):
        organization = get_object_or_404(Organization, pk=kwargs['org_id'])
        kwargs['organization'] = organization
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = True
        context['organization'] = self.kwargs['organization']
        context['auto_fill_data'] = {
            'ad': {
                'username_attribute': "sAMAccountName",
                'rdn_attribute': "cn",
                'uuid_attribute': "objectGUID",
                'user_obj_classes': "person, organizationalPerson, user",
            },
            'other': {
                'username_attribute': "uid",
                'rdn_attribute': "uid",
                'uuid_attribute': "entryUUID",
                'user_obj_classes': "inetOrgPerson, organizationalPerson",
            },
        }
        return context

    def form_valid(self, form):
        # TODO: ensure all proper checks are in place either here or elsewhere
        current_time = now()
        form.instance.last_modified = now()
        form.instance.organization = self.kwargs['organization']
        form.instance.ldap_credential = form.cleaned_data['ldap_password']
        return super().form_valid(form)
        organization = self.kwargs['organization']
        # TODO: ensure Realm existence upon activating feature! And on Org creation (if feature is active)
        realm, created = Realm.objects.get_or_create(
            realm_id=organization.slug,
            organization=organization,
            defaults={'last_modified': current_time},
        )
        payload = form.instance.get_payload_dict()
        add_or_update_ldap_conf(payload)  # TODO: consider moving request elsewhere, else add error-handling!


class LDAPUpdateView(LoginRequiredMixin, UpdateView):

    model = LDAPConfig
    template_name = 'import_services/ldap_edit.html'
    success_url = reverse_lazy('organization-list')
    form_class = LDAPEditForm

    def setup(self, request, *args, **kwargs):
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_new'] = False
        context['organization'] = self.object.organization
        return context

    def form_valid(self, form):
        form.instance.ldap_credential = form.cleaned_data['ldap_password']
        payload = form.instance.get_payload_dict()
        add_or_update_ldap_conf(payload)  # TODO: consider moving request elsewhere, else add error-handling!
        return super().form_valid(form)
