import structlog

from django.db import transaction
from django.db.utils import DataError
from prometheus_client import Summary, start_http_server
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread

from ..checkup_collector import checkup_message_received_raw
from ..checkup_collector import problem_message_recieved_raw
from ..status_collector import status_message_received_raw

logger = structlog.get_logger(__name__)
SUMMARY = Summary("os2datascanner_collector_runner_admin",
                  "Messages through collector runner")


class CollectorRunner(PikaPipelineThread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        start_http_server(9091)

    def handle_message(self, routing_key, body):
        with SUMMARY.time():
            logger.debug(
                    "raw message received",
                    routing_key=routing_key,
                    body=body)
            try:
                with transaction.atomic():
                    if routing_key == "os2ds_status":
                        yield from status_message_received_raw(body)
                    elif routing_key == "os2ds_checkups":
                        yield from checkup_message_received_raw(body)
                    elif routing_key == "os2ds_problems":
                        yield from problem_message_recieved_raw(body)
            except DataError as de:
                # DataError occurs when something went wrong trying to select
                # or create/update data in the database. Often regarding
                # ScheduledCheckups it is related to the json data. For now, we
                # only log the error message.
                logger.error(
                        "Could not get or create object, due to DataError",
                        error=de)
