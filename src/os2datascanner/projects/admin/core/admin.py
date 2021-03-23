from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .forms import ClientAdminForm
from .models import Client, Administrator


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
