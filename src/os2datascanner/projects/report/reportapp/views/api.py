import json
import structlog
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import View

from ..models.documentreport_model import DocumentReport
from .views import LoginRequiredMixin


logger = structlog.get_logger()


def set_status_1(body):
    pk = body.get("report_id")
    status_value = body.get("new_status")

    try:
        status = DocumentReport.ResolutionChoices(status_value).value
    except ValueError:
        return {
            "status": "fail",
            "message": "invalid status identifier {0}".format(status_value)
        }

    report = DocumentReport.objects.get(pk=pk)
    if report is None:
        return {
            "status": "fail",
            "message": "report {0} does not exist".format(pk)
        }
    elif report.resolution_status is not None:
        return {
            "status": "fail",
            "message": "report {0} already has a status".format(pk)
        }

    report.resolution_status = status_value
    try:
        report.clean()
    except ValidationError:
        return {
            "status": "fail",
            "message": "validation failed"
        }

    report.save()
    return {
        "status": "ok"
    }


def error_1(body):
    return {
        "status": "fail",
        "message": "action was missing or did not identify an endpoint"
    }


api_endpoints = {
    "set-status-1": set_status_1
}


class JSONAPIView(LoginRequiredMixin):
    def post(self, request):
        return JsonResponse(self.get_data(request))

    def http_method_not_allowed(self, request):
        r = JsonResponse({
            "status": "fail",
            "message": "method not allowed"
        })
        r.status_code = 405
        return r

    def get_data(self, request):
        try:
            body = json.loads(request.body.decode("utf-8"))
            logger.info("API call for user {0}".format(request.user), **body)
            return api_endpoints.get(body.get("action"), error_1)(body)
        except json.JSONDecodeError:
            return {
                "status": "fail",
                "message": "payload was not a valid JSON object"
            }
