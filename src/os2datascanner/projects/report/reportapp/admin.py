from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models.roles.remediator_model import Remediator
from .models.roles.defaultrole_model import DefaultRole
from .models.aliases.adsidalias_model import ADSIDAlias
from .models.aliases.emailalias_model import EmailAlias
from .models.aliases.webdomainalias_model import WebDomainAlias
from .models.documentreport_model import DocumentReport
from .models.organization_model import Organization
from .models.userprofile_model import UserProfile

# Register your models here.

admin.site.register(DocumentReport)

@admin.register(ADSIDAlias)
class ADSIDAliasAdmin(admin.ModelAdmin):
    list_display = ('sid', 'user', )

@admin.register(EmailAlias)
class EmailAliasAdmin(admin.ModelAdmin):
    list_display = ('address', 'user', )

@admin.register(WebDomainAlias)
class WebDomainAliasAdmin(admin.ModelAdmin):
    list_display = ('domain', 'user', )

@admin.register(DefaultRole)
class DefaultRoleAdmin(admin.ModelAdmin):
    list_display = ('user', )

@admin.register(Remediator)
class RemediatorAdmin(admin.ModelAdmin):
    list_display = ('user', )

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    # This object is owned by another system (admin)
    # We can't change instances directly - only view

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
