import json
import base64
import urllib.parse

from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from ..models.graphgrant import GraphGrant


class MSGraphGrantReceptionView(LoginRequiredMixin, View):
    SUCCESS_PARAMS = ("tenant", "state", "admin_consent",)
    FAILURE_PARAMS = ("error", "error_description")

    def get(self, request):
        state = json.loads(
                base64.b64decode(
                        # "e30=" is Base64 for "{}", since you asked
                        request.GET.get("state", "e30=")))
        if not all(k in state for k in ("red", "org",)):
            return HttpResponse("state_missing", status=400)

        redirect = reverse(state["red"], kwargs=state.get("rdk", {}))
        parameters = ""
        if all(k in request.GET for k in self.SUCCESS_PARAMS):
            # The remote server has given us our grant -- hooray! Store it in
            # the database before we redirect to the original URL
            GraphGrant.objects.get_or_create(
                    tenant_id=request.GET["tenant"],
                    organization_id=state["org"])
        elif any(k in request.GET for k in self.FAILURE_PARAMS):
            # The remote server has not given us our grant -- boo. Pass the
            # error details back to the original URL for rendering
            parameters = "?" + urllib.parse.urlencode(request.GET)

        return HttpResponseRedirect(redirect + parameters)
