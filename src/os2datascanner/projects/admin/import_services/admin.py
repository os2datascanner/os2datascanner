from django.contrib import admin

from .models import LDAPConfig, Realm

# Register your models here.

for model in [LDAPConfig, Realm]:
    admin.site.register(model)


class ImportedAdmin(admin.ModelAdmin):
    readonly_fields = ('imported_id', 'last_import')
