import json
import structlog
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import View

from os2datascanner.utils.system_utilities import time_now
from ..models.documentreport import DocumentReport
from ..utils import iterate_queryset_in_batches

logger = structlog.get_logger()


def set_status_1(username, body):
    """ Used for handling a match by a DocumentReport ID and resolutionstatus value.
    Supports handling one match at a time.
    May eventually be deprecated"""
    pk = body.get("report_id")
    status_value = body.get("new_status")

    try:
        DocumentReport.ResolutionChoices(status_value).value
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


def set_status_2(username, body):
    """ Refines set_status_1 functionality.
    Retrieves a list of DocumentReport id's and a handling-status value
    from template.
    Converts list to queryset and bulk_updates DocumentReport model"""

    doc_rep_pk = body.get("report_id")
    status_value = body.get("new_status")
    doc_reports = DocumentReport.objects.filter(pk__in=doc_rep_pk)

    logger.info(
        "User changing match status",
        user=username,
        status=DocumentReport.ResolutionChoices(status_value),
        **body,
    )

    if not doc_reports.exists():
        logger.warning(
            "Could not find reports for status change",
            user=username,
            **body,
        )
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
                dr.resolution_time = time_now()

        DocumentReport.objects.bulk_update(batch, ['resolution_status', 'resolution_time'])
        return {
            "status": "ok"
        }


def error_1(username, body):
    logger.warning("User called non-existing endpoint", user=username, **body)
    return {
        "status": "fail",
        "message": "action was missing or did not identify an endpoint"
    }


api_endpoints = {
    "set-status-1": set_status_1,
    "set-status-2": set_status_2
}


class JSONAPIView(LoginRequiredMixin, View):
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
            return api_endpoints.get(body.get("action"), error_1)(str(request.user), body)
        except json.JSONDecodeError:
            return {
                "status": "fail",
                "message": "payload was not a valid JSON object"
            }
