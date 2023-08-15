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
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
"""Admin form configuration."""

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from os2datascanner.engine2.rules.rule import Rule

from .models.authentication import Authentication
from .models.apikey import APIKey
from .models.usererrorlog import UserErrorLog
from .models.rules.cprrule import CPRRule, TurboCPRRule
from .models.rules.namerule import NameRule
from .models.rules.regexrule import RegexRule, RegexPattern
from .models.rules.customrule import CustomRule
from .models.rules.addressrule import AddressRule
from .models.scannerjobs.scanner import (ScanStatus,
                                         ScheduledCheckup,
                                         ScanStatusSnapshot)
from .models.scannerjobs.msgraph import (MSGraphMailScanner,
                                         MSGraphFileScanner,
                                         MSGraphCalendarScanner,
                                         MSGraphTeamsFileScanner)
from .models.scannerjobs.webscanner import WebScanner
from .models.scannerjobs.filescanner import FileScanner
from .models.scannerjobs.exchangescanner import ExchangeScanner
from .models.scannerjobs.dropboxscanner import DropboxScanner
from .models.scannerjobs.googledrivescanner import GoogleDriveScanner
from .models.scannerjobs.gmail import GmailScanner


@admin.register(Authentication)
class AuthenticationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'domain')
    list_display_links = ('pk', 'username')


@admin.register(CPRRule)
@admin.register(TurboCPRRule)
@admin.register(NameRule)
@admin.register(RegexRule)
@admin.register(AddressRule)
class RuleAdmin(admin.ModelAdmin):
    list_filter = ('sensitivity',)
    list_display = ('name', 'organization', 'sensitivity')


# Used to create custom field for customrule in django-changeform
class CustomRuleWidget(forms.widgets.Widget):
    template_name = "components/admin-widgets/rule-builder.html"

    class Media:
        # Css is only caught when using --force-recreate on admin
        css = {
            'all': ('admin/css/custom-widgets/rule-builder.css',)
        }


class CustomRuleForm(forms.ModelForm):
    list_filter = ('sensitivity',)
    list_display = ('name', 'organization', 'sensitivity')

    class Meta:
        model = CustomRule
        exclude = ()
        fields = ("__all__")
        widgets = {
            '_rule': CustomRuleWidget(),
        }

    # Check that POST-response is valid using clean_<field_name>
    def clean__rule(self):
        try:
            Rule.from_json_object(self.cleaned_data["_rule"])
        except Exception:
            raise forms.ValidationError(
                _("Rule cannot be compiled by scanner"))

        if str(self.cleaned_data["_rule"]).count("'type': 'cpr'") > 1:
            raise forms.ValidationError(
                _("CPR rule should not be used more than once"))

        if str(self.cleaned_data["_rule"]).count("'type': 'ordered-wordlist'") > 1:
            raise forms.ValidationError(
                _("Health-information rule should not be used more than once"))

        return self.cleaned_data["_rule"]


@admin.register(CustomRule)
class CustomRuleAdmin(admin.ModelAdmin):
    form = CustomRuleForm


@admin.register(RegexPattern)
class RegexPatternAdmin(admin.ModelAdmin):
    list_display = ('pattern_string', 'regex')


@admin.register(WebScanner)
@admin.register(FileScanner)
@admin.register(DropboxScanner)
@admin.register(ExchangeScanner)
@admin.register(MSGraphMailScanner)
@admin.register(MSGraphFileScanner)
@admin.register(MSGraphCalendarScanner)
@admin.register(MSGraphTeamsFileScanner)
@admin.register(GoogleDriveScanner)
@admin.register(GmailScanner)
class ScannerAdmin(admin.ModelAdmin):
    list_display = ('name', 'validation_status')

    # For excluding orgunits.
    include_orgunit_scanners = [ExchangeScanner,
                                MSGraphMailScanner,
                                MSGraphFileScanner,
                                MSGraphCalendarScanner,
                                MSGraphTeamsFileScanner]

    def get_fields(self, request, obj=None):
        """Only show organizational units if relevant."""

        if type(obj) not in self.include_orgunit_scanners:
            self.exclude = ('org_unit', )

        return super().get_fields(request, obj=obj)


@admin.register(ScheduledCheckup)
class ScheduledCheckupAdmin(admin.ModelAdmin):
    list_filter = ('scanner',)


for _cls in (APIKey,):
    admin.site.register(_cls)


class UserErrorLogForm(forms.ModelForm):
    def clean(self):
        if self.cleaned_data["is_new"] and self.cleaned_data["is_removed"]:
            raise forms.ValidationError(_("An errorlog cannot both be new and removed"))

        return self.cleaned_data


@admin.register(UserErrorLog)
class UserErrorLogAdmin(admin.ModelAdmin):
    model = UserErrorLog
    form = UserErrorLogForm
    list_display = (
        'user_friendly_error_message',
        'path',
        'scan_status',
        'organization',
        'is_removed',
        'is_new'
    )
    list_display_links = (
        'user_friendly_error_message',
        'path'
    )
    readonly_fields = (
        'path',
        'user_friendly_error_message',
        'error_message',
        'scan_status',
        'organization',)
    fields = (
        'path',
        'user_friendly_error_message',
        'error_message',
        'scan_status',
        'organization',
        'is_new',
        'is_removed'
    )

    actions = ('mark_new', 'mark_not_new', 'mark_removed', 'mark_not_removed',)

    @admin.action(description=_("Change new-status to True"))
    def mark_new(self, request, query_set):
        query_set.filter(is_removed=False).update(is_new=True)
        messages.add_message(request, messages.INFO, _(
            "Changed {qs_count} elements new-status to True. "
            "Note: if the element has its is_removed attribute set to True, "
            "it has not been changed.")
                .format(qs_count=query_set.count()))

    @admin.action(description=_("Change new-status to False"))
    def mark_not_new(self, request, query_set):
        query_set.update(is_new=False)
        messages.add_message(request, messages.INFO, _(
            "Changed {qs_count} elements new-status to False")
                .format(qs_count=query_set.count()))

    @admin.action(description=_("Change removed-status to True"))
    def mark_removed(self, request, query_set):
        query_set.update(is_removed=True, is_new=False)
        messages.add_message(request, messages.INFO, _(
            "Changed {qs_count} elements removed-status to True")
                .format(qs_count=query_set.count()))

    @admin.action(description=_("Change removed-status to False"))
    def mark_not_removed(self, request, query_set):
        query_set.update(is_removed=False)
        messages.add_message(request, messages.INFO, _(
            "Changed {qs_count} elements removed-status to False")
                .format(qs_count=query_set.count()))


@admin.register(ScanStatus)
class ScanStatusAdmin(admin.ModelAdmin):
    list_display = ('scanner', 'pk', 'start_time', 'resolved')
    list_display_links = ('scanner', 'pk', 'start_time')
    model = ScanStatus
    readonly_fields = ('fraction_explored', 'fraction_scanned',
                       'estimated_completion_time', 'start_time', 'last_modified',)
    fields = ('scan_tag', 'scanner', 'total_sources', 'explored_sources',
              'fraction_explored', 'total_objects', 'scanned_objects', 'matches_found',
              'fraction_scanned', 'scanned_size', 'estimated_completion_time',
              'start_time', 'last_modified', 'resolved',)

    actions = ('change_resolvestatus_false', 'change_resolvestatus_true')

    @admin.action(description=_("Change resolved-status to True"))
    def change_resolvestatus_true(self, request, query_set):
        query_set.update(resolved=True)
        messages.add_message(request, messages.INFO, _(
            "Changed {qs_count} elements resolved-status to True")
                .format(qs_count=query_set.count()))

    @admin.action(description=_("Change resolved-status to False"))
    def change_resolvestatus_false(self, request, query_set):
        query_set.update(resolved=False)
        messages.add_message(request, messages.INFO, _(
            "Changed {qs_count} elements resolved-status to False")
                .format(qs_count=query_set.count()))


@admin.register(ScanStatusSnapshot)
class ScanStatusSnapshotAdmin(admin.ModelAdmin):
    model = ScanStatusSnapshot
    list_display = ('pk', 'scan_status', 'time_stamp', 'fraction_scanned')
    list_display_links = ('pk', 'scan_status')
    readonly_fields = ('scan_status', 'time_stamp', 'total_sources',
                       'explored_sources', 'fraction_explored', 'total_objects',
                       'scanned_objects', 'fraction_scanned', 'scanned_size')


admin.site.unregister(Group)
