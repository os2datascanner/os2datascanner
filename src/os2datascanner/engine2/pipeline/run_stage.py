from prometheus_client import start_http_server

from ..model.core import SourceManager
from .utilities.args import (make_common_argument_parser,
        make_sourcemanager_configuration_block)
from .utilities.pika import PikaPipelineRunner
from .utilities.systemd import notify_ready, notify_stopping
from . import explorer, processor, matcher, tagger, exporter, worker


__module_mapping = {
    "explorer": explorer,
    "processor": processor,
    "matcher": matcher,
    "tagger": tagger,
    "exporter": exporter,
    "worker": worker
}


def main():
    parser = make_common_argument_parser()
    parser.description = ("Runs an OS2datascanner pipeline stage.")

    parser.add_argument(
            "stage",
            choices=("explorer", "processor", "matcher",
                    "tagger", "exporter", "worker",))

    make_sourcemanager_configuration_block(parser)

    args = parser.parse_args()
    module = __module_mapping[args.stage]

    if args.enable_metrics:
        start_http_server(args.prometheus_port)

    class GenericRunner(PikaPipelineRunner):
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return module.message_received_raw(body, channel, source_manager)

    with SourceManager(width=args.width) as source_manager:
        with GenericRunner(
                read=module.__reads_queues__,
                write=module.__writes_queues__,
                heartbeat=6000) as runner:
            try:
                print("Start")
                notify_ready()
                runner.run_consumer()
            finally:
                print("Stop")
                notify_stopping()


if __name__ == "__main__":
    main()
