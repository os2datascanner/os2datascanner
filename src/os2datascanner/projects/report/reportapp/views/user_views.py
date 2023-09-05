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
from django.views.generic import DetailView
from django.http import HttpResponse, Http404

from ..models.roles.role import Role
from ...organizations.models import Account


class AccountView(LoginRequiredMixin, DetailView):
    template_name = "user.html"
    context_object_name = "account"
    model = Account

    def get_object(self, queryset=None):
        if self.kwargs.get("slug") is None:
            try:
                self.kwargs["slug"] = self.request.user.account.slug
            except Account.DoesNotExist:
                raise Http404()
        elif not (self.request.user.is_superuser or
                  self.kwargs.get("slug") == self.request.user.account.slug):
            raise Http404()
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.object.user

        roles = Role.get_user_roles_or_default(user)
        user_roles = [role._meta.verbose_name for role in roles]

        context["user"] = user
        context["user_roles"] = user_roles
        context["aliases"] = self.object.aliases.all()

        return context

    def post(self, request, *args, **kwargs):
        bool_field_status = request.POST.get("contact_check", False) == "checked"

        account = self.get_object()
        account.contact_person = bool_field_status
        account.save()

        return HttpResponse()
