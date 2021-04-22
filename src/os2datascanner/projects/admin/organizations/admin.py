from django.contrib import admin

from .models import Organization, OrganizationalUnit, Account, Position, Alias

# Register your models here.

for model in [Organization, OrganizationalUnit, Account, Position, Alias]:
    admin.site.register(model)
