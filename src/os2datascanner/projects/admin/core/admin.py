from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import ClientAdminForm
from .models import Client, Administrator, BackgroundJob
from .models.background_job import JobState


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    """Controls behaviour for Django admin pages for the Administrator model."""

    fields = ('user', 'client',)
    list_display = ('__str__', 'user', 'client',)
    search_fields = ('user__username', 'client__name',)
    list_filter = (
        ('client', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = True

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        if change:
            form.base_fields['client'].empty_label = None
        else:
            choice_limits = {'administrator_for__isnull': True}
            field = form.base_fields['user']
            field.limit_choices_to = choice_limits
            field.help_text = _(
                'Users who are already Administrators are not shown.'
            )
            if field._queryset.filter(**choice_limits).count() == 0:
                field.empty_label = _('-- No valid users available --')

        return form

    def get_readonly_fields(self, request, obj=None):
        """Return tuple of read-only fields.

        On edit of existing relation, add user to read-only tuple.
        """

        readonly = super().get_readonly_fields(request, obj)
        if obj:  # Editing existing relation
            readonly = readonly + ('user',)
        return readonly


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Controls behaviour for Django admin pages for the Client model."""
    form = ClientAdminForm
    list_display = ('name', 'contact_email', 'contact_phone', 'uuid',)
    list_display_links = ('name', 'uuid',)
    search_fields = ('name', 'contact_email', 'uuid',)


def progress(obj):
    value = None
    caption = None

    if obj.exec_state in (
            JobState.WAITING, JobState.CANCELLED, JobState.FAILED):
        caption = obj.exec_state.label
    elif obj.exec_state in (
            JobState.RUNNING, JobState.CANCELLING, JobState.FINISHED):
        value = obj.progress
        if value is not None:
            caption = f"{value * 100:.0f}%"
        else:
            if obj.exec_state != JobState.FINISHED:
                # Put the progress bar into indeterminate mode (with an empty
                # value) if we don't have anything more specific to show
                value = ""
            caption = obj.exec_state.label

    result = ""
    if value is not None:
        result += """<progress max="1.0" value="{value}">{value}</progress>"""
        if caption:
            result += "<br />"
    if caption:
        result += "{caption}"
    return format_html(result, value=value, caption=caption)


@admin.register(BackgroundJob)
class BackgroundJobAdmin(admin.ModelAdmin):
    list_display = ('pk', 'exec_state', progress)
    readonly_fields = (progress, "created_at", "changed_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        hdp = super().has_delete_permission(request, obj)
        # Deletion is not safe if the job is in a running state
        if obj:
            hdp = hdp and obj.exec_state not in (
                    JobState.RUNNING, JobState.CANCELLING)
        return hdp

    def get_queryset(self, request):
        return BackgroundJob.objects.all().select_subclasses()
