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
import structlog
from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from django import forms
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

from .utilities.msgraph_utilities import (create_outlook_category_for_account,
                                          OutlookCategoryName, update_outlook_category_for_account,
                                          delete_outlook_category_for_account,
                                          get_msgraph_mail_document_reports,
                                          get_tenant_id_from_document_report,
                                          categorize_existing_emails_from_account)
from ...organizations.models.aliases import AliasType
from ...organizations.models import Account, AccountOutlookSetting

logger = structlog.get_logger()


class AccountOutlookSettingForm(forms.ModelForm):
    class Meta:
        model = AccountOutlookSetting
        fields = ['categorize_email', 'match_colour', 'false_positive_colour']


class AccountOutlookSettingView(LoginRequiredMixin, DetailView):
    template_name = "components/outlook_category_settings.html"
    context_object_name = "account"
    model = Account

    def post(self, request, *args, **kwargs):  # noqa C901, CCR001
        account = self.get_object()

        htmx_trigger = self.request.headers.get("HX-Trigger-Name")
        if htmx_trigger == "categorize_existing":
            categorize_existing_emails_from_account(
                account,
                OutlookCategoryName.Match
            )

            success_message = _("Successfully categorized your emails!")
            logger.info(f"{account} categorized their emails manually")
            messages.add_message(
                request,
                messages.SUCCESS,
                success_message
            )

        if request.POST.get("outlook_setting", False):  # We're doing stuff in the outlook settings
            categorize_check = request.POST.get("categorize_check", False) == "on"
            match_colour = request.POST.get("match_colour")
            false_positive_colour = request.POST.get("false_positive_colour")

            acc_ol_settings, c = AccountOutlookSetting.objects.update_or_create(
                account_username=account.username,
                defaults={
                    "account": account,
                    "categorize_email": categorize_check,
                }
            )

            if categorize_check:
                # UUID's on Categories not set: Create
                if not acc_ol_settings.match_category_uuid:
                    try:
                        match_resp = create_outlook_category_for_account(account,
                                                                         OutlookCategoryName.Match,
                                                                         AccountOutlookSetting.
                                                                         OutlookCategoryColour(
                                                                             match_colour))
                        acc_ol_settings.match_colour = match_colour
                        acc_ol_settings.match_category_uuid = match_resp.json().get("id")
                    except PermissionDenied as e:
                        error_message = _("Couldn't create category! Please make sure"
                                          " the match category doesn't already exist.")
                        logger.error(f"{error_message} \n {e}")
                        messages.add_message(
                            request,
                            messages.ERROR,
                            error_message)

                if not acc_ol_settings.false_positive_category_uuid:
                    try:
                        false_p_resp = create_outlook_category_for_account(
                            account,
                            OutlookCategoryName.FalsePositive,
                            AccountOutlookSetting.OutlookCategoryColour(false_positive_colour))

                        acc_ol_settings.false_positive_colour = false_positive_colour
                        acc_ol_settings.false_positive_category_uuid = false_p_resp.json().get("id")
                    except PermissionDenied as e:
                        error_message = _("Couldn't create category! Please make sure"
                                          " the false positive category doesn't already exist.")
                        logger.error(f"{error_message} \n {e}")
                        messages.add_message(
                            request,
                            messages.ERROR,
                            error_message
                        )

                # Else, we can assume that we're updating.
                if match_colour != acc_ol_settings.match_colour:
                    try:
                        update_outlook_category_for_account(account,
                                                            acc_ol_settings.match_category_uuid,
                                                            AccountOutlookSetting.
                                                            OutlookCategoryColour(match_colour)
                                                            )

                        acc_ol_settings.match_colour = (AccountOutlookSetting.
                                                        OutlookCategoryColour(match_colour))
                    except PermissionDenied as e:
                        error_message = _("Couldn't update match category colour!")
                        logger.error(f"{error_message} \n {e}")
                        messages.add_message(
                            request,
                            messages.ERROR,
                            error_message
                        )

                if false_positive_colour != acc_ol_settings.false_positive_colour:
                    try:
                        update_outlook_category_for_account(
                            account,
                            acc_ol_settings.false_positive_category_uuid,
                            AccountOutlookSetting.OutlookCategoryColour(false_positive_colour))

                        acc_ol_settings.false_positive_colour = (AccountOutlookSetting.
                                                                 OutlookCategoryColour(
                                                                     false_positive_colour))
                    except PermissionDenied as e:
                        error_message = _("Couldn't update false positive category colour!")
                        logger.error(f"{error_message} \n {e}")
                        messages.add_message(
                            request,
                            messages.ERROR,
                            error_message
                        )

            if not categorize_check and (acc_ol_settings.match_category_uuid
                                         and acc_ol_settings.false_positive_category_uuid):

                try:
                    delete_outlook_category_for_account(account,
                                                        acc_ol_settings.match_category_uuid
                                                        )
                    acc_ol_settings.match_category_uuid = None
                except PermissionDenied as e:
                    error_message = _("Couldn't delete match category!")
                    logger.error(f"{error_message} \n {e}")
                    messages.add_message(
                        request,
                        messages.ERROR,
                        error_message
                    )

                try:
                    delete_outlook_category_for_account(account,
                                                        acc_ol_settings.false_positive_category_uuid
                                                        )
                    acc_ol_settings.false_positive_category_uuid = None
                except PermissionDenied as e:
                    error_message = _("Couldn't delete false positive category")
                    logger.error(f"{error_message} \n {e}")
                    messages.add_message(
                        request,
                        messages.ERROR,
                        error_message
                    )

            acc_ol_settings.save()

        # Used to make Django's messages framework and HTMX play ball.
        response = HttpResponse()
        response.write(
            render_to_string(
                template_name="components/snackbar.html",
                context={"messages": get_messages(request)},
                request=request
            )
        )

        return response

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
        acc_ol_settings, c = AccountOutlookSetting.objects.get_or_create(
            account=self.object,
            account_username=self.object.username)
        context["categorize_enabled"] = acc_ol_settings.categorize_email
        context["colour_presets"] = AccountOutlookSettingForm()


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

        if settings.MSGRAPH_ALLOW_WRITE and self.object.organization.has_categorize_permission():
            acc_ol_settings, c = AccountOutlookSetting.objects.get_or_create(
                account=self.object,
                account_username=self.object.username)
            context["has_categorize_permission"] = True
            try:
                document_report = get_msgraph_mail_document_reports(self.object).last()
                get_tenant_id_from_document_report(document_report)
                context["tenant_id_retrievable"] = True
            except PermissionDenied as e:
                context["tenant_id_retrievable"] = False
                logger.warning(f"Can't retrieve tenant id: {e}")

            context["categorize_enabled"] = acc_ol_settings.categorize_email
            context["colour_presets"] = AccountOutlookSettingForm()

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
