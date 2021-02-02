import json
import time
from uuid import uuid4
from pathlib import Path

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


def api_endpoint(func):
    def runner(body, start_response):
        it = func(body)
        status = next(it)
        start_response(status, [
                ("Content-Type", "text/plain; charset=ascii"),
                ("Content-Disposition", "inline")])
        for obj in it:
            yield json.dumps(obj).encode("ascii") + b"\n"
    return runner


def resource_endpoint(path):
    def runner(body, start_response):
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


@api_endpoint
def scan_1(body):
    if not body:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "parameters missing"
        }

    if "source" not in body or "rule" not in body:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "either \"source\" or \"rule\" was missing"
        }
        return

    source = Source.from_json_object(body["source"])
    if not source:
        yield "400 Bad Request"
        yield {
            "status": "fail",
            "message": "\"source\" could not be understood as a Source"
        }
        return
    elif (settings.server["permitted_sources"]
            and source.type_label not in settings.server["permitted_sources"]):
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
            scan_tag=str(uuid4()),
            source=source,
            rule=rule,
            configuration={},
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


endpoints = {
    "/openapi.yaml": resource_endpoint("openapi.yaml"),
    "/dummy/1": dummy_1,
    "/scan/1": scan_1
}


def application(env, start_response):
    server_token = settings.server["token"]
    if not server_token:
        start_response("500 Internal Server Error", [])
        yield b"""\
<html><body><h1>500 Internal Server Error</h1>\
<p>No API token configured.</body></html>"""
        return

    if not "HTTP_AUTHORIZATION" in env:
        start_response("401 Unauthorized", [
                ("WWW-Authentication", "Bearer realm=\"api\"")])
        return
    else:
        authentication = env["HTTP_AUTHORIZATION"].split()
        if not authentication[0] == "Bearer" or len(authentication) != 2:
            start_response("400 Bad Request", [
                    ("WWW-Authentication",
                            "Bearer realm=\"api\" error=\"invalid_request\"")])
            return
        elif authentication[1] != server_token:
            start_response("401 Unauthorized", [
                    ("WWW-Authentication",
                            "Bearer realm=\"api\" error=\"invalid_token\"")])
            return

    try:
        body = None
        parameters = env["wsgi.input"].read().decode("ascii")
        if parameters:
            body = json.loads(parameters)
        runner = endpoints.get(env.get("PATH_INFO"), error_1)
    except json.JSONDecodeError:
        runner = catastrophe_1

    yield from runner(body, start_response)
