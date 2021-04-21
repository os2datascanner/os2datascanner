from django.contrib import admin

from os2datascanner.projects.admin.import_services.admin import ImportedAdmin

from .models import Organization, OrganizationalUnit, Account, Position, Alias

# Register your models here.

for model in [OrganizationalUnit, Position, Account, Alias]:
    admin.site.register(model, ImportedAdmin)

admin.site.register(Organization)
