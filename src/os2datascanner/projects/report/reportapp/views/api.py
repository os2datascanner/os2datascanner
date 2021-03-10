import json
import structlog
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import View

from ..models.documentreport_model import DocumentReport
from .views import LoginRequiredMixin
from ..utils import iterate_queryset_in_batches

logger = structlog.get_logger()


def set_status_1(body):
    """ Retrieves a list of DocumentReport id's and a handling-status value
    from template.
    Converts list to queryset and bulk_updates DocumentReport model"""

    doc_rep_pk = body.get("report_id")
    status_value = body.get("new_status")

    doc_reports = DocumentReport.objects.filter(pk__in=doc_rep_pk)

    if not doc_reports:
        return {
            "status": "fail",
            "message": "unable to populate list of doc reports"
        }

    for batch in iterate_queryset_in_batches(10000, doc_reports):
        for dr in batch:
            if dr.resolution_status is not None:
                return {
                    "status": "fail",
                    "message": "report {0} already has a status".format(dr.pk)
                }
            else:
                dr.resolution_status = status_value

        DocumentReport.objects.bulk_update(batch, ['resolution_status'])
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
