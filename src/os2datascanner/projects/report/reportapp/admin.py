from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models.documentreport import DocumentReport

from os2datascanner.projects.report.organizations.models import Organization, Account
# Register your models here.


class ScannerJobFilter(admin.SimpleListFilter):
    title = _("scanner job")

    parameter_name = "scanner"

    def lookups(self, request, model_admin):
        # Get all (scanner job name, scanner primary key) tuples
        objects = DocumentReport.objects.order_by("-scanner_job_pk").only(
                "scanner_job_name", "scanner_job_pk").distinct(
                "scanner_job_name", "scanner_job_pk")
        return (
            (o.scanner_job_pk, o.scanner_job_name) for o in objects
        )

    def queryset(self, request, queryset):
        v = self.value()
        if v is not None:
            return queryset.filter(scanner_job_pk=v)


@admin.register(DocumentReport)
class DocumentReportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number_of_matches',
        'organization',
        'scanner_job_name',
        'aliases',
        'resolution_status',
        'resolution_time', 'only_notify_superadmin')

    list_filter = (
        'organization',
        ScannerJobFilter,)

    def aliases(self, dr):
        return ", ".join([alias_relation.account.username
                          for alias_relation in dr.alias_relation.all()])

    def get_queryset(self, request):
        return super(DocumentReportAdmin, self).get_queryset(request).select_related(
            'organization').prefetch_related('alias_relation')


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
