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
from django.contrib.auth.models import Group

from .models.authentication_model import Authentication
from .models.organization_model import Organization, APIKey
from .models.rules.cprrule_model import CPRRule
from .models.rules.namerule_model import NameRule
from .models.rules.regexrule_model import RegexRule, RegexPattern
from .models.rules.addressrule_model import AddressRule
from .models.scannerjobs.scanner_model import ScanStatus, ScheduledCheckup
from .models.scannerjobs.msgraph_models import MSGraphMailScanner
from .models.scannerjobs.webscanner_model import WebScanner
from .models.scannerjobs.filescanner_model import FileScanner
from .models.scannerjobs.exchangescanner_model import ExchangeScanner
from .models.scannerjobs.dropboxscanner_model import DropboxScanner
from .models.scannerjobs.googledrivescanner_model import GoogleDriveScanner
from .models.scannerjobs.gmail_model import GmailScanner


@admin.register(Authentication)
class AuthenticationAdmin(admin.ModelAdmin):
    list_display = ('username', 'domain')


@admin.register(CPRRule)
@admin.register(NameRule)
@admin.register(RegexRule)
@admin.register(AddressRule)
class RuleAdmin(admin.ModelAdmin):
    list_filter = ('sensitivity',)
    list_display = ('name', 'organization', 'sensitivity')


@admin.register(RegexPattern)
class RegexPatternAdmin(admin.ModelAdmin):
    list_display = ('pattern_string', 'regex')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'uuid')
    readonly_fields = ('uuid',)
    fields = ('name', 'contact_email', 'contact_phone', 'do_notify_all_scans')


@admin.register(WebScanner)
@admin.register(FileScanner)
@admin.register(DropboxScanner)
@admin.register(ExchangeScanner)
@admin.register(MSGraphMailScanner)
@admin.register(GoogleDriveScanner)
@admin.register(GmailScanner)
class ScannerAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'validation_status')


for _cls in [APIKey, ScheduledCheckup]:
    admin.site.register(_cls)


@admin.register(ScanStatus)
class ScanStatusAdmin(admin.ModelAdmin):
    model = ScanStatus
    readonly_fields = ('fraction_explored', 'fraction_scanned',
                       'estimated_completion_time',)
    fields = ('scan_tag', 'scanner', 'total_sources', 'explored_sources',
              'fraction_explored', 'total_objects', 'scanned_objects',
              'fraction_scanned', 'scanned_size', 'estimated_completion_time',)


admin.site.unregister(Group)
