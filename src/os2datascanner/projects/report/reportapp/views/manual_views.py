from django.views.generic import TemplateView

from ...organizations.models.organization import MSGraphWritePermissionChoices


class ManualMainView(TemplateView):
    template_name = "manual.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorization"] = (
            self.request.user.account.organization.msgraph_write_permissions in (
                MSGraphWritePermissionChoices.ALL, MSGraphWritePermissionChoices.CATEGORIZE))
        return context
