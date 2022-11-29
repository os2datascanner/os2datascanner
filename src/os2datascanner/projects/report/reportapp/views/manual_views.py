from django.views.generic import TemplateView

from ..models.roles.dpo import DataProtectionOfficer
from ..utils import convert_context_to_email_body


class ManualMainView(TemplateView):
    template_name = "manual.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TODO: This information is only for the support button: Move it to its own view!
        context["dpo_contacts"] = DataProtectionOfficer.objects.filter(contact_person=True)
        context["email_body"] = convert_context_to_email_body(context, self.request)
        return context
