from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models.roles.remediator import Remediator
from .models.roles.leader import Leader
from .models.roles.dpo import DataProtectionOfficer
from .models.roles.defaultrole import DefaultRole
from .models.documentreport import DocumentReport

from os2datascanner.projects.report.organizations.models import Organization, Account
# Register your models here.

admin.site.register(DocumentReport)


# Solution for avoiding m2m relations to get cleared
# Source(StackOverflow): https://bit.ly/31qwMk9
# This takes all the DocumentReports that match the Alias and adds them on save.
class AliasAdmin(admin.ModelAdmin):

    raw_id_fields = ['match_relation']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.match_relation:
            reports = DocumentReport.objects.filter(
                raw_metadata__metadata__contains={
                    str(obj.key): str(obj)
                })
            form.cleaned_data['match_relation'] = reports


@admin.register(DefaultRole)
class DefaultRoleAdmin(admin.ModelAdmin):
    list_display = ('user', )


@admin.register(Remediator)
class RemediatorAdmin(admin.ModelAdmin):
    list_display = ('user', )


@admin.register(Leader)
class LeaderAdmin(admin.ModelAdmin):
    list_display = ('user', )


@admin.register(DataProtectionOfficer)
class DataProtectionOfficerAdmin(admin.ModelAdmin):
    list_display = ('user', )


class ProfileInline(admin.TabularInline):

    """Inline class for user accounts."""

    model = Account
    extra = 1
    can_delete = False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)

        if db_field.name == 'organization':
            if not request.user.is_superuser:
                field.queryset = Organization.objects.filter(
                    name=request.user.account.organization.name
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
                (_('Personal info'),  # noqa: F821
                 {'fields': ('first_name', 'last_name', 'email')}),
                (_('Important dates'), {'fields': ('last_login',  # noqa: F821
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
            account__organization=request.user.account.organization
        )


admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
