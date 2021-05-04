import sys
import signal
import argparse
import traceback
import logging
from prometheus_client import start_http_server
from .utilities.prometheus import prometheus_summary


from ..model.core import SourceManager
from .utilities.pika import PikaPipelineRunner
from .utilities.systemd import notify_ready, notify_stopping
from . import explorer, processor, matcher, tagger, exporter, worker


def backtrace(signal, frame):
    """send `SIGURS1` to print the stacktrace,
    kill -USR1 <pid>
    """
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

__loglevels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
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
    parser.add_argument(
            "--log",
            default="info",
            help=(
                "Set logging level. Example --log debug', default='info'"
            ),
            choices=("critical", "error", "warn", "warning", "info", "debug",)
        )

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

    # leave all loggers from external libraries at default(WARNING) level.
    # change formatting to include datestamp
    fmt = "%(asctime)s;%(name)s;%(levelname)s;%(message)s"
    logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
    # set level for root logger
    logger = logging.getLogger("os2datascanner")
    logger.setLevel(__loglevels[args.log])

    if args.enable_metrics:
        start_http_server(args.prometheus_port)

    class GenericRunner(PikaPipelineRunner):
        @prometheus_summary(
            "os2datascanner_pipeline_{0}".format(args.stage),
            module.PROMETHEUS_DESCRIPTION)
        def handle_message(self, body, *, channel=None):
            # this is very verbose.
            # logger.debug("{0}\t{1}".format(channel, body)
            if args.debug:
                print(channel, body)
            return module.message_received_raw(body, channel, source_manager)

    with SourceManager(width=args.width) as source_manager:
        with GenericRunner(
                read=module.READS_QUEUES,
                write=module.WRITES_QUEUES,
                heartbeat=6000) as runner:
            try:
                logger.info("Start")
                notify_ready()
                runner.run_consumer()
            finally:
                logger.info("Stop")
                notify_stopping()


if __name__ == "__main__":
    main()
