import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from os2datascanner.engine2.rules.logical import OrRule
from ..models.rules.rule_model import Rule
from ..models.scannerjobs.scanner_model import Scanner


def get_rule_1(body):
    """Returns the name and JSON representation of a rule."""

    pk = body.get("rule_id") if body else None
    if not isinstance(pk, int):
        return {
            "status": "fail",
            "message": "\"rule_id\" was missing or invalid"
        }

    try:
        rule = Rule.objects.select_subclasses().get(pk=pk)
    except Rule.DoesNotExist:
        return {
            "status": "fail",
            "message": "rule {0} does not exist".format(pk)
        }

    return {
        "status": "ok",
        "name": rule.name,
        "rule": rule.make_engine2_rule()
    }


def get_scanner_1(body):
    """Returns a summary of a scanner job: its name, the (censored) Sources
    that it will scan, and the rule that will be executed."""

    pk = body.get("scanner_id") if body else None
    if not isinstance(pk, int):
        return {
            "status": "fail",
            "message": "\"scanner_id\" was missing or invalid"
        }

    try:
        scanner = Scanner.objects.select_subclasses().get(pk=pk)
    except Scanner.DoesNotExist:
        return {
            "status": "fail",
            "message": "scanner {0} does not exist".format(pk)
        }

    rule_generator = (r.make_engine2_rule()
            for r in scanner.rules.all().select_subclasses())
    return {
        "status": "ok",
        "name": scanner.name,
        "rule": OrRule.make(*rule_generator).to_json_object(),
        "sources": list(s.censor().to_json_object()
                for s in scanner.generate_sources())
    }


def error_1(body):
    return {
        "status": "fail",
        "message": "path was missing or did not identify an endpoint"
    }


def catastrophe_1(body):
    return {
        "status": "fail",
        "message": "payload was not a valid JSON object"
    }


api_endpoints = {
    "get-rule/1": get_rule_1,
    "get-scanner/1": get_scanner_1
}


@method_decorator(csrf_exempt, name="dispatch")
class JSONAPIView(View):
    def post(self, request, *, path):
        return JsonResponse(self.get_data(request, path=path))

    def http_method_not_allowed(self, request, *, path):
        r = JsonResponse({
            "status": "fail",
            "message": "method not supported"
        })
        r.status_code = 405
        return r

    def get_data(self, request, *, path):
        try:
            body = None
            if request.body:
                body = json.loads(request.body.decode("utf-8"))
            handler = api_endpoints.get(path, error_1)
        except json.JSONDecodeError:
            handler = catastrophe_1

        return handler(body)
