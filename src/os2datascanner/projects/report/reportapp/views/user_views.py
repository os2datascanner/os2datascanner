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

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from ...organizations.models import Account
from ...organizations.models.aliases import AliasType


class AccountView(LoginRequiredMixin, DetailView):
    template_name = "user.html"
    context_object_name = "account"
    model = Account

    def get_object(self, queryset=None):
        if self.kwargs.get("pk") is None:
            try:
                self.kwargs["pk"] = self.request.user.account.pk
            except Account.DoesNotExist:
                raise Http404()
        elif not (self.request.user.is_superuser or
                  self.kwargs.get("pk") == self.request.user.account.pk):
            raise PermissionDenied
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.object.user
        context["user"] = user
        context["user_roles"] = [_("Remediator")] if self.object.is_remediator else None
        context["aliases"] = self.object.aliases.exclude(_alias_type=AliasType.REMEDIATOR)

        return context

    def post(self, request, *args, **kwargs):
        bool_field_status = request.POST.get("contact_check", False) == "checked"

        account = self.get_object()
        account.contact_person = bool_field_status
        account.save()

        return HttpResponse()
