from django.views.generic import TemplateView
from django.db.models import Q

from ..utils import convert_context_to_email_body
from ...organizations.models import Account
from os2datascanner.core_organizational_structure.models.position import Role


class SupportButtonView(TemplateView):
    template_name = "components/service.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dpo_contacts"] = Account.objects.filter(Q(positions__role=Role.DPO) & Q(
            positions__unit__in=self.request.user.account.units.all()))
        context["email_body"] = convert_context_to_email_body(self.request)
        return context
