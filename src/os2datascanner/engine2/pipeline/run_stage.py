import sys
import signal
import argparse
import traceback
from prometheus_client import start_http_server
from .utilities.prometheus import prometheus_summary


from ..model.core import SourceManager
from .utilities.pika import PikaPipelineRunner
from .utilities.systemd import notify_ready, notify_stopping
from . import explorer, processor, matcher, tagger, exporter, worker


def backtrace(signal, frame):
    print("Got SIGUSR1, printing stacktrace:", file=sys.stderr)
    traceback.print_stack()


__module_mapping = {
    "explorer": explorer,
    "processor": processor,
    "matcher": matcher,
    "tagger": tagger,
    "exporter": exporter,
    "worker": worker
}


def _compatibility_main(stage):
    print("{0}: warning: this command is deprecated,"
            " use run_stage.py instead".format(sys.argv[0]))
    sys.argv = [sys.argv[0], stage]
    main()


def main():
    signal.signal(signal.SIGUSR1, backtrace)

    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Runs an OS2datascanner pipeline stage.")
    parser.add_argument(
            "--debug",
            action="store_true",
            help="print all incoming messages to the console")

    monitoring = parser.add_argument_group("monitoring")
    monitoring.add_argument(
            "--enable-metrics",
            action="store_true",
            help="enable exporting of metrics")
    monitoring.add_argument(
            "--prometheus-port",
            metavar="PORT",
            help="the port to serve OpenMetrics data.",
            default=9091)

    parser.add_argument(
            "stage",
            choices=("explorer", "processor", "matcher",
                    "tagger", "exporter", "worker",))

    configuration = parser.add_argument_group("configuration")
    configuration.add_argument(
            "--width",
            type=int,
            metavar="SIZE",
            help="allow each source to have at most %(metavar) "
                    "simultaneous open sub-sources",
            default=3)

    args = parser.parse_args()
    module = __module_mapping[args.stage]

    if args.enable_metrics:
        start_http_server(args.prometheus_port)

    class GenericRunner(PikaPipelineRunner):
        @prometheus_summary(
            "os2datascanner_pipeline_{0}".format(args.stage),
            module.PROMETHEUS_DESCRIPTION)
        def handle_message(self, body, *, channel=None):
            if args.debug:
                print(channel, body)
            return module.message_received_raw(body, channel, source_manager)

    with SourceManager(width=args.width) as source_manager:
        with GenericRunner(
                read=module.READS_QUEUES,
                write=module.WRITES_QUEUES,
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
