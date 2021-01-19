import json
import time
from uuid import uuid4

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


def dummy_1(body):
    yield "200 OK"
    yield {
        "status": "ok"
    }


def error_1(body):
    yield "400 Bad Request"
    yield {
        "status": "fail",
        "message": "\"action\" was missing or did not identify an endpoint"
    }


def scan_1(body):
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
                    if c2 in ("os2ds_matches", "os2ds_metadata",):
                        for c3, m3 in exporter_mrr(m2, c2, sm):
                            yield m3


def catastrophe_1(body):
    yield "400 Really Very Bad Request Indeed"
    yield {
        "status": "fail",
        "message": "payload was not a valid JSON object"
    }


api_endpoints = {
    "dummy-1": dummy_1,
    "scan-1": scan_1
}


def application(env, start_response):
    try:
        body = json.loads(env["wsgi.input"].read().decode("ascii"))
        it = api_endpoints.get(body.get("action"), error_1)(body)
    except json.JSONDecodeError:
        it = catastrophe_1(None)

    status = next(it)
    start_response(status, [
            ("Content-Type", "application/jsonl")])
    for obj in it:
        yield json.dumps(obj).encode("ascii") + b"\n"
