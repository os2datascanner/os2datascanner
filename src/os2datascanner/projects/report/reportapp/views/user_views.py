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
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django import forms
from django.http import HttpResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .utilities.msgraph_utilities import (create_outlook_category_for_account,
                                          OutlookCategoryName, update_outlook_category_for_account,
                                          delete_outlook_category_for_account)
from ...organizations.models.aliases import AliasType
from ...organizations.models import Account, AccountOutlookSetting


class AccountOutlookSettingForm(forms.ModelForm):
    class Meta:
        model = AccountOutlookSetting
        fields = ['categorize_email', 'match_colour', 'false_positive_colour']


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

        if settings.MSGRAPH_ALLOW_WRITE:
            acc_ol_settings, c = AccountOutlookSetting.objects.get_or_create(
                account=self.object,
                account_username=self.object.username)
            context["categorize_enabled"] = acc_ol_settings.categorize_email
            context["colour_presets"] = AccountOutlookSettingForm()

        user = self.object.user
        context["user"] = user
        context["user_roles"] = [_("Remediator")] if self.object.is_remediator else None
        context["aliases"] = self.object.aliases.exclude(_alias_type=AliasType.REMEDIATOR)

        return context

    def post(self, request, *args, **kwargs):  # noqa CCR001
        bool_field_status = request.POST.get("contact_check", False) == "checked"
        account = self.get_object()
        account.contact_person = bool_field_status
        account.save()

        if request.POST.get("outlook_setting", False):  # We're doing stuff in the outlook settings
            categorize_check = request.POST.get("categorize_check", False) == "checked"
            match_colour = request.POST.get("match_colour")
            false_positive_colour = request.POST.get("false_positive_colour")

            # TODO: if you dont have any msgraph reports, you can't create labels because
            #  we can get any tenant id
            # .. but htmx and django messages framework dont play ball well together,
            # because its using cookies / the request cycle.. So we're not warning.

            acc_ol_settings, _ = AccountOutlookSetting.objects.update_or_create(
                account_username=account.username,
                defaults={
                    "account": account,
                    "categorize_email": categorize_check,
                }
            )

            if categorize_check:
                # UUID's on Categories not set: Create
                if not acc_ol_settings.match_category_uuid:
                    match_resp = create_outlook_category_for_account(account,
                                                                     OutlookCategoryName.Match,
                                                                     AccountOutlookSetting.
                                                                     OutlookCategoryColour(
                                                                         match_colour))
                    acc_ol_settings.match_colour = match_colour
                    acc_ol_settings.match_category_uuid = match_resp.json().get("id")
                    acc_ol_settings.save()

                if not acc_ol_settings.false_positive_category_uuid:
                    false_p_resp = create_outlook_category_for_account(
                        account,
                        OutlookCategoryName.FalsePositive,
                        AccountOutlookSetting.OutlookCategoryColour(false_positive_colour))
                    acc_ol_settings.false_positive_colour = false_positive_colour
                    acc_ol_settings.false_positive_category_uuid = false_p_resp.json().get("id")
                    acc_ol_settings.save()

                # Else, we can assume that we're updating.
                if match_colour != acc_ol_settings.match_colour:
                    update_outlook_category_for_account(account,
                                                        acc_ol_settings.match_category_uuid,
                                                        AccountOutlookSetting.
                                                        OutlookCategoryColour(match_colour)
                                                        )
                if false_positive_colour != acc_ol_settings.false_positive_colour:
                    update_outlook_category_for_account(
                        account,
                        acc_ol_settings.false_positive_category_uuid,
                        AccountOutlookSetting.OutlookCategoryColour(false_positive_colour))

            # TODO: Not very well written; if we can't delete the first one, we won't even try
            # the second. Same goes for logic above
            # Unchecked, delete categories.
            if not categorize_check and (acc_ol_settings.match_category_uuid
                                         and acc_ol_settings.false_positive_category_uuid):
                delete_outlook_category_for_account(account,
                                                    acc_ol_settings.match_category_uuid
                                                    )
                acc_ol_settings.match_category_uuid = None
                delete_outlook_category_for_account(account,
                                                    acc_ol_settings.false_positive_category_uuid
                                                    )
                acc_ol_settings.false_positive_category_uuid = None
                acc_ol_settings.save()

        return HttpResponse()
