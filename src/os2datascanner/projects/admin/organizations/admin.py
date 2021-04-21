from django.contrib import admin

from .models import Organization, OrganizationalUnit, Account, Position

# Register your models here.

for model in [Organization, OrganizationalUnit, Account, Position]:
    admin.site.register(model)
