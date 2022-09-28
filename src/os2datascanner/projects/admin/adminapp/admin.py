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

from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from .models.authentication import Authentication
from .models.apikey import APIKey
from .models.usererrorlog import UserErrorLog
from .models.rules.cprrule import CPRRule
from .models.rules.namerule import NameRule
from .models.rules.regexrule import RegexRule, RegexPattern
from .models.rules.customrule import CustomRule
from .models.rules.addressrule import AddressRule
from .models.scannerjobs.scanner import (ScanStatus,
                                         ScheduledCheckup,
                                         ScanStatusSnapshot)
from .models.scannerjobs.msgraph import (MSGraphMailScanner,
                                         MSGraphFileScanner,
                                         MSGraphCalendarScanner)
from .models.scannerjobs.webscanner import WebScanner
from .models.scannerjobs.filescanner import FileScanner
from .models.scannerjobs.exchangescanner import ExchangeScanner
from .models.scannerjobs.dropboxscanner import DropboxScanner
from .models.scannerjobs.googledrivescanner import GoogleDriveScanner
from .models.scannerjobs.gmail import GmailScanner


@admin.register(Authentication)
class AuthenticationAdmin(admin.ModelAdmin):
    list_display = ('username', 'domain')


@admin.register(CPRRule)
@admin.register(NameRule)
@admin.register(RegexRule)
@admin.register(CustomRule)
@admin.register(AddressRule)
class RuleAdmin(admin.ModelAdmin):
    list_filter = ('sensitivity',)
    list_display = ('name', 'organization', 'sensitivity')


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
@admin.register(GoogleDriveScanner)
@admin.register(GmailScanner)
class ScannerAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'validation_status')

    # For excluding orgunits.
    include_orgunit_scanners = [ExchangeScanner,
                                MSGraphMailScanner,
                                MSGraphFileScanner,
                                MSGraphCalendarScanner]

    def get_fields(self, request, obj=None):
        """Only show organizational units if relevant."""

        if type(obj) not in self.include_orgunit_scanners:
            self.exclude = ('org_unit', )

        return super().get_fields(request, obj=obj)


for _cls in [APIKey, ScheduledCheckup]:
    admin.site.register(_cls)


@admin.register(UserErrorLog)
class UserErrorLogAdmin(admin.ModelAdmin):
    model = UserErrorLog
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
        'is_removed')

    actions = ('mark_new', 'mark_not_removed',)

    def mark_new(self, request, queryset):
        queryset.update(is_new=True)

    def mark_not_removed(self, request, queryset):
        queryset.update(is_removed=False)


@admin.action(description=_('Change marked resolved=False'))
def change_resolvestatus_false(self, request, query_set):
    query_set.update(resolved=False)
    messages.add_message(
        request,
        messages.INFO,
        _("Changed {qs_count} elements resolved-status to False").format(qs_count=query_set.count())
    )


@admin.action(description=_('Change marked resolved=True'))
def change_resolvestatus_true(self, request, query_set):
    query_set.update(resolved=True)
    messages.add_message(
        request,
        messages.INFO,
        _("Changed {qs_count} elements resolved-status to True").format(qs_count=query_set.count())
    )


@admin.register(ScanStatus)
class ScanStatusAdmin(admin.ModelAdmin):
    list_display = ('scanner', 'pk', 'start_time', 'resolved')
    list_display_links = ('scanner', 'pk', 'start_time')
    model = ScanStatus
    readonly_fields = ('fraction_explored', 'fraction_scanned',
                       'estimated_completion_time', 'start_time', 'last_modified',)
    fields = ('scan_tag', 'scanner', 'total_sources', 'explored_sources',
              'fraction_explored', 'total_objects', 'scanned_objects',
              'fraction_scanned', 'scanned_size', 'estimated_completion_time',
              'start_time', 'last_modified', 'resolved',)
    actions = [change_resolvestatus_false, change_resolvestatus_true]


@admin.register(ScanStatusSnapshot)
class ScanStatusSnapshotAdmin(admin.ModelAdmin):
    model = ScanStatusSnapshot
    readonly_fields = ('scan_status', 'time_stamp', 'total_sources',
                       'explored_sources', 'fraction_explored', 'total_objects',
                       'scanned_objects', 'fraction_scanned', 'scanned_size')


admin.site.unregister(Group)
