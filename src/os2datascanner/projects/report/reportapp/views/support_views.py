from django.views.generic import TemplateView
from django.db.models import Q
from django.http import Http404

from ..utils import convert_context_to_email_body
from ...organizations.models import Account
from os2datascanner.core_organizational_structure.models.position import Role
from os2datascanner.core_organizational_structure.models.organization import (
    SupportContactChoices, DPOContactChoices)


class SupportButtonView(TemplateView):
    template_name = "components/service.html"

    def dispatch(self, request, *args, **kwargs):
        self.org = request.user.account.organization
        if self.org.show_support_button:
            return super().dispatch(request, *args, **kwargs)
        else:
            raise Http404()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dpo_contacts"] = Account.objects.filter(Q(positions__role=Role.DPO) & Q(
            positions__unit__in=self.request.user.account.units.all()))
        context["email_body"] = convert_context_to_email_body(self.request)

        # Send organization settings to the template
        context["organization"] = self.org
        context["SupportContactChoices"] = SupportContactChoices
        context["DPOContactChoices"] = DPOContactChoices

        return context
