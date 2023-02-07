from django.views.generic import TemplateView

from ..utils import convert_context_to_email_body
from ..models.roles.dpo import DataProtectionOfficer


class SupportButtonView(TemplateView):
    template_name = "components/service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dpo_contacts"] = DataProtectionOfficer.objects.filter(contact_person=True)
        context["email_body"] = convert_context_to_email_body(self.request)
        return context
