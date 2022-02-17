#!/usr/bin/env python3

import sys

from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.pipeline.exporter import censor_outgoing_message
from os2datascanner.engine2.pipeline.utilities.pika import PikaPipelineThread


class_mapping = {
    "os2ds_checkups": messages.MatchesMessage,
    "os2ds_conversions": messages.ConversionMessage,
    "os2ds_handles": messages.HandleMessage,
    "os2ds_matches": messages.MatchesMessage,
    "os2ds_metadata": messages.MetadataMessage,
    "os2ds_problems": messages.ProblemMessage,
    "os2ds_representations": messages.RepresentationMessage,
    "os2ds_scan_specs": messages.ScanSpecMessage,
    "os2ds_status": messages.StatusMessage,
}


class Printer(PikaPipelineThread):
    def handle_message(self, routing_key, body):
        if routing_key == "os2ds_results":
            routing_key = body["origin"]

        message = None
        try:
            if routing_key in class_mapping:
                message = class_mapping[routing_key].from_json_object(body)
        except Exception:
            pass

        if not message:
            print(
                    "warning: unrecognised message format, printing uncensored"
                    " content", file=sys.stderr)
            print(body)
        else:
            print(
                    "information: message format recognised, printing censored"
                    " content", file=sys.stderr)
            print(censor_outgoing_message(message).to_json_object())

        # Enqueueing a stop command before handle_message returns ensures that
        # we'll disconnect before we acknowledge recept of this message
        self.enqueue_stop()
        yield from []


def main():
    for queue in sys.argv[1:]:
        print(f"Waiting for a message on queue {queue}...")
        with Printer(read={queue}) as p:
            p.run_consumer()


if __name__ == '__main__':
    main()
