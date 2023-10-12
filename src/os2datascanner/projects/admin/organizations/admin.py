from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from os2datascanner.projects.admin.import_services.admin import ImportedAdmin

from .models import Organization, OrganizationalUnit, Account, Position, Alias

# Register your models here.

for model in [OrganizationalUnit, Position]:
    admin.site.register(model, ImportedAdmin)


@admin.register(Alias)
class AliasAdmin(ImportedAdmin):
    """ Controls behaviour in Django Admin
           for the Alias model"""
    fields = ('account', '_alias_type', '_value',
              'last_import_requested', 'last_import'
              )
    list_display = ('account', '_alias_type', '_value', 'last_import')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """ Controls behaviour in Django Admin
         for the Organization model"""

    fieldsets = [
        (
            None,
            {
                "fields": ('name', 'slug', 'client', 'contact_email',
                           'contact_phone', 'email_notification_schedule',)
            },
        ),
        (
            _("Tab access"),
            {
                "fields": ('leadertab_access', 'dpotab_access')
            },
        ),
        (
            _("Support button settings"),
            {
                "fields": ('show_support_button', 'support_contact_method',
                           'support_name', 'support_value', 'dpo_contact_method',
                           'dpo_name', 'dpo_value')
            }
        )
    ]
    list_display = ('name', 'client', 'contact_email', 'contact_phone')
    search_fields = ('name', 'client__name',)


@admin.register(Account)
class AccountAdmin(ImportedAdmin):
    """ Controls behaviour in Django Admin
     for the Account model"""

    # TODO: Consider if 'units' is needed here?
    #  At the time of writing units does not work
    fields = ('username', 'first_name', 'last_name',
              'organization', 'manager', 'imported_id', 'last_import',
              'is_superuser'
              )
    list_display = ('username', 'first_name', 'last_name',
                    'organization', 'last_import',
                    )
    search_fields = ('username', 'first_name', 'last_name',
                     'organization__name',
                     )
    list_filter = (
        'organization',
    )
