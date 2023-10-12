# Register your models here.
from django.contrib import admin


from .models.account import Account
from .models.aliases import Alias
from .models.organization import Organization
from .models.organizational_unit import OrganizationalUnit
from .models.position import Position


class ReadOnlyAdminMixin:
    """ Defines that model is read only through django admin interface
        Useful here because objects are owned by another system (admin)
        We can't change instances directly - only view"""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Alias)
class AliasAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_filter = ["_alias_type"]
    list_display = ('user', 'account', '_alias_type', '_value')
    readonly_fields = ('user', 'account', '_alias_type', '_value')


@admin.register(Account)
class AccountAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'organization', 'manager', 'uuid')
    readonly_fields = ('username', 'first_name', 'last_name', 'organization', 'manager', 'uuid')


@admin.register(Organization)
class OrganizationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'uuid',)
    readonly_fields = ('name', 'uuid',)


@admin.register(OrganizationalUnit)
class OrganizationalUnitAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'uuid', 'parent', 'organization')
    readonly_fields = ('name', 'uuid', 'parent', 'organization')


@admin.register(Position)
class PositionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('account', 'unit', 'role')
    readonly_fields = ('account', 'unit', 'role')
