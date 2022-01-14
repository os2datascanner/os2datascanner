import json
from uuid import uuid4
from pathlib import Path

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.rules.rule import Rule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.explorer import (
        message_received_raw as explorer_mrr)
from os2datascanner.engine2.pipeline.worker import (
        message_received_raw as worker_mrr)
from os2datascanner.engine2.pipeline.exporter import (
        message_received_raw as exporter_mrr)
from . import settings


def requires_token(func):
    def runner(env, start_response, body):
        server_token = settings.server["token"]
        if not server_token:
            start_response("500 Internal Server Error", [])
            yield b"""\
<html><body><h1>500 Internal Server Error</h1>\
<p>No API token configured.</body></html>"""
            return

        if "HTTP_AUTHORIZATION" not in env:
            start_response("401 Unauthorized", [
                    ("WWW-Authentication", "Bearer realm=\"api\"")])
            return
        else:
            authentication = env["HTTP_AUTHORIZATION"].split()
            if not authentication[0] == "Bearer" or len(authentication) != 2:
                start_response("400 Bad Request", [
                        ("WWW-Authentication",
                         "Bearer realm=\"api\""
                         " error=\"invalid_request\"")])
                return
            elif authentication[1] != server_token:
                start_response("401 Unauthorized", [
                        ("WWW-Authentication",
                         "Bearer realm=\"api\""
                         " error=\"invalid_token\"")])
                return
        yield from func(env, start_response, body)
    return runner


def api_endpoint(func):
    @requires_token
    def runner(env, start_response, body):
        it = func(body)
        status = next(it)
        start_response(status, [
                ("Content-Type", "text/plain; charset=ascii"),
                ("Content-Disposition", "inline")])
        for obj in it:
            yield json.dumps(obj).encode("ascii") + b"\n"
    return runner


def resource_endpoint(path):
    def runner(env, start_response, body):
        with Path(__file__).parent.joinpath(path).open("rb") as fp:
            content = fp.read()
        start_response("200 OK", [
                ("Content-Length", str(len(content)))])
        yield content
    return runner


@api_endpoint
def dummy_1(body):
    yield "200 OK"
    yield {
        "status": "ok"
    }


@api_endpoint
def error_1(body):
    yield "400 Bad Request"
    yield {
        "status": "fail",
        "message": "path was missing or did not identify an endpoint"
    }


def _get_top(s: Source) -> Source:
    while s.handle:
        s = s.handle.source
    return s


@api_endpoint
def scan_1(body):  # noqa: CCR001
    if not body:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "parameters missing"
        }
        return

    if "source" not in body or "rule" not in body:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "either \"source\" or \"rule\" was missing"
        }
        return

    source = Source.from_json_object(body["source"])
    top_type = _get_top(source).type_label
    if not source:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "\"source\" could not be understood as a Source"
        }
        return
    elif (settings.server["permitted_sources"]
            and top_type not in settings.server["permitted_sources"]):
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "cannot scan Sources "
                       "of type \"{0}\"".format(source.type_label)
        }
        return

    rule = Rule.from_json_object(body["rule"])
    if not rule:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "\"rule\" could not be understood as a Rule"
        }
        return

    yield "200 OK"

    message = messages.ScanSpecMessage(
            scan_tag=messages.ScanTagFragment(
                    time=time_now(),
                    user=None,
                    scanner=messages.ScannerFragment(
                            pk=0,
                            name="API server demand scan"),
                    organisation=messages.OrganisationFragment(
                            name="API server",
                            uuid=uuid4())),
            source=source,
            rule=rule,
            configuration=body.get("configuration", {}),
            progress=None).to_json_object()

    with SourceManager() as sm:
        for c1, m1 in explorer_mrr(message, "os2ds_scan_specs", sm):
            if c1 in ("os2ds_conversions",):
                for c2, m2 in worker_mrr(m1, c1, sm):
                    if c2 in ("os2ds_matches",
                              "os2ds_metadata", "os2ds_problems",):
                        yield from (m3 for _, m3 in exporter_mrr(m2, c2, sm))
            elif c1 in ("os2ds_problems",):
                yield from (m2 for _, m2 in exporter_mrr(m1, c1, sm))


@api_endpoint
def catastrophe_1(body):
    yield "400 Really Very Bad Request Indeed"
    yield {
        "status": "fail",
        "message": "payload was not a valid JSON object"
    }


def unsupported_1(env, start_response, body):
    start_response("405 Method Not Supported", [])
    yield json.dumps({
        "status": "fail",
        "message": "method not supported"
    }).encode("ascii")


def option_endpoint(path):
    def runner(env, start_response, body):
        methods = endpoints.get(path).keys()
        start_response("204 No Content", [
                ("Access-Control-Allow-Methods", ", ".join(methods)),
                ("Access-Control-Allow-Headers", "authorization, content-type")
        ])
        yield from []
    return runner


endpoints = {
    "/openapi.yaml": {
        "GET": resource_endpoint("openapi.yaml")
    },
    "/dummy/1": {
        "POST": dummy_1,
        "OPTIONS": option_endpoint("/dummy/1")
    },
    "/scan/1": {
        "POST": scan_1,
        "OPTIONS": option_endpoint("/scan/1")
    }
}


def application(env, start_response):
    try:
        body = None
        parameters = env["wsgi.input"].read().decode("ascii")
        if parameters:
            body = json.loads(parameters)
        endpoint = endpoints.get(env.get("PATH_INFO"))
        if endpoint:
            runner = endpoint.get(env.get("REQUEST_METHOD"), unsupported_1)
        else:
            runner = error_1
    except json.JSONDecodeError:
        runner = catastrophe_1

    def _response_wrapper(status, headers):
        return start_response(status, headers + [
                        ("Access-Control-Allow-Origin", "*")])
    yield from runner(env, _response_wrapper, body)
