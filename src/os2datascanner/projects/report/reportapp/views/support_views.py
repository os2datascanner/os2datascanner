from django.views.generic import TemplateView

from ..utils import convert_context_to_email_body
from ...organizations.models.position import Position
from os2datascanner.core_organizational_structure.models.position import Role


class SupportButtonView(TemplateView):
    template_name = "components/service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dpo_contacts"] = Position.objects.filter(
            role=Role.DPO,
            account__contact_person=True,
            account__organization=self.request.user.account.organization
        )
        context["email_body"] = convert_context_to_email_body(self.request)
        return context
