import json

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
        "message": "action was missing or did not identify an endpoint"
    }


def catastrophe_1(body):
    yield "400 Really Very Bad Request Indeed"
    yield {
        "status": "fail",
        "message": "payload was not a valid JSON object"
    }


api_endpoints = {
    "dummy-1": dummy_1
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
