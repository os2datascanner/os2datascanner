import json

from . import settings


def application(env, start_response):
    start_response("200 OK", [
            ("Content-Type", "application/json")])
    yield(json.dumps({"status": "error"}).encode("ascii"))
