from django.contrib import admin
from .models import LDAPConfig, MSGraphConfiguration, OS2moConfiguration, Realm


# Register your models here.

class ImportedAdmin(admin.ModelAdmin):
    readonly_fields = ('imported_id', 'last_import')


@admin.register(LDAPConfig)
class LDAPConfigAdmin(admin.ModelAdmin):
    """ Controls behaviour in Django Admin
               for the LDAPConfig model"""
    list_display = ('vendor', 'connection_url', 'connection_protocol',
                    'search_scope',
                    )


admin.site.register(MSGraphConfiguration)


admin.site.register(OS2moConfiguration)


@admin.register(Realm)
class RealmAdmin(admin.ModelAdmin):
    """ Controls behaviour in Django Admin
               for the Realm model"""
    list_display = ('realm_id', 'organization',)
