#!/usr/bin/env python
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
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from django.http import HttpResponse

from ..utils import convert_context_to_email_body
from ..models.roles.role import Role
from ..models.roles.dpo import DataProtectionOfficer


class UserView(TemplateView, LoginRequiredMixin):
    template_name = "user.html"
    context_object_name = "user"
    model = User

    def get_queryset(self):
        return User.objects.get(username=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        roles_qs = Role.get_user_roles_or_default(self.request.user)
        user_roles = [role._meta.verbose_name for role in roles_qs]

        context["is_dpo"] = "DPO" in user_roles
        context["is_contact_person"] = roles_qs.filter(
            dataprotectionofficer__contact_person=True).exists()
        context["user_roles"] = user_roles
        context["aliases"] = User.objects.get(username=self.request.user).aliases.all()

        # TODO: This information is only for the support button: Move it to its own view!
        context["email_body"] = convert_context_to_email_body(context, self.request)
        context["dpo_contacts"] = DataProtectionOfficer.objects.filter(contact_person=True)
        return context

    def post(self, request, *args, **kwargs):
        bool_field_status = request.POST.get("contact_check", False) == "checked"
        DataProtectionOfficer.objects.filter(
            user=self.request.user).update(
            contact_person=bool_field_status)

        return HttpResponse()
