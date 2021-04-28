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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Admin form configuration."""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

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
from .models.userprofile_model import UserProfile


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


class ProfileInline(admin.TabularInline):

    """Inline class for user profiles."""

    model = UserProfile
    extra = 1
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'organization':
            if not request.user.is_superuser:
                field.queryset = Organization.objects.filter(
                    name=request.user.profile.organization.name
                )
                field.empty_label = None

        return field


class MyUserAdmin(UserAdmin):

    """Custom user admin class."""

    inlines = [ProfileInline]
    can_delete = False

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            self.fieldsets = (
                (None,
                 {'fields': ('username', 'password', 'is_active')}),
                (_('Personal info'),
                 {'fields': ('first_name', 'last_name', 'email')}),
                (_('Important dates'), {'fields': ('last_login',
                                                   'date_joined')}),
            )

            self.exclude = ['is_superuser', 'permissions', 'groups']
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        """Only allow users belonging to same organization to be edited."""

        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs
        return qs.filter(
            profile__organization=request.user.profile.organization
        )


admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
