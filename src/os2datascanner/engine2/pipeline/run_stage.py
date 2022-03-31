import argparse
import logging
import os
import random
import signal
import sys
import traceback
import pstats
from collections import deque

from prometheus_client import Info, Summary, start_http_server

from os2datascanner.utils import profiling
from ... import __version__
from ..model.core import SourceManager
from . import explorer, exporter, matcher, messages, processor, tagger, worker
from .utilities.pika import PikaPipelineThread, RejectMessage


# __name__ is "__main__" in this context, which isn't quite what we want for
# our position in the logging hierarchy
logger = logging.getLogger("os2datascanner.engine2.pipeline.run_stage")


def backtrace(signal, frame):
    print("Got SIGUSR1, printing stacktrace:", file=sys.stderr)
    traceback.print_stack()


_module_mapping = {
    "explorer": explorer,
    "processor": processor,
    "matcher": matcher,
    "tagger": tagger,
    "exporter": exporter,
    "worker": worker
}


_loglevels = {
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


def restart_process():
    """Clean exit, used to release all ressources used by this process and children.

    Restart will be handled by kubernetes or docker, depending on the setup."""
    sys.exit(0)


class GenericRunner(PikaPipelineThread):
    def __init__(self,
                 source_manager: SourceManager, *args,
                 stage: str, module, limit, **kwargs):
        super().__init__(
                *args, **kwargs,
                read=module.READS_QUEUES,
                write=module.WRITES_QUEUES,
                prefetch_count=module.PREFETCH_COUNT)
        self._module = module
        self._summary = Summary(
                f"os2datascanner_pipeline_{stage}",
                self._module.PROMETHEUS_DESCRIPTION)
        self._source_manager = source_manager

        self._cancelled = deque()

        self._limit = limit
        self._count = 0

    def _handle_command(self, routing_key, body):
        command = messages.CommandMessage.from_json_object(body)

        if command.abort:
            self._cancelled.appendleft(command.abort)

        if command.log_level:
            logging.getLogger("os2datascanner").setLevel(
                    command.log_level)

        if command.profiling is not None:
            profiling.print_stats(pstats.SortKey.CUMULATIVE, silent=True)
            if command.profiling:
                profiling.enable_profiling()
                logger.info("enabling profiling")
            else:
                profiling.disable_profiling()
                logger.info("disabling profiling")

        yield from []

    def _handle_content(self, routing_key, body):
        raw_scan_tag = body.get("scan_tag")
        if not raw_scan_tag and "scan_spec" in body:
            raw_scan_tag = body["scan_spec"]["scan_tag"]

        if raw_scan_tag:
            scan_tag = messages.ScanTagFragment.from_json_object(
                    raw_scan_tag)
            if scan_tag in self._cancelled:
                logger.debug(
                        f"scan {raw_scan_tag} is cancelled, "
                        "ignoring")
                raise RejectMessage(requeue=False)

        yield from self._module.message_received_raw(
                body, routing_key, self._source_manager)

    def handle_message(self, routing_key, body):
        with self._summary.time():
            logger.debug(f"{routing_key}: {str(body)}")
            if routing_key == "":
                yield from self._handle_command(routing_key, body)
            else:
                yield from self._handle_content(routing_key, body)

    def after_message(self, routing_key, body):
        # Check to see if we've met our quota and should restart
        self._count += 1
        if self._limit is not None and self._count >= self._limit:
            global restarting
            restarting = True
            self.enqueue_stop()


restarting = False


def main():
    signal.signal(signal.SIGUSR1, backtrace)

    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="Runs an OS2datascanner pipeline stage.")
    parser.add_argument(
            "--log",
            default="info",
            help="change the level at which log messages will be printed",
            choices=_loglevels.keys()
        )
    parser.add_argument(
            "--profile",
            action="store_true",
            help="record and print profiling output"
        )
    parser.add_argument(
            "stage",
            choices=("explorer", "processor", "matcher",
                     "tagger", "exporter", "worker",))

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

    configuration = parser.add_argument_group("configuration")
    configuration.add_argument(
            "--width",
            type=int,
            metavar="SIZE",
            help="allow each source to have at most %(metavar) "
                    "simultaneous open sub-sources",
            default=3)
    configuration.add_argument(
            "--single-cpu",
            action="store_true",
            help="instruct the scheduler to run this stage, and its"
                 " subprocesses, on a single CPU, either picked at random"
                 " or based on the SCHEDULE_ON_CPU environment variable")
    configuration.add_argument(
            "--restart-after",
            metavar="COUNT",
            dest="limit",
            type=int,
            default=None,
            help="re-execute this stage after it has handled %(metavar)s"
                    " messages")

    args = parser.parse_args()
    module = _module_mapping[args.stage]

    # leave all loggers from external libraries at default(WARNING) level.
    # change formatting to include datestamp
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
    # set level for root logger
    root_logger = logging.getLogger("os2datascanner")
    root_logger.setLevel(_loglevels[args.log])
    root_logger.info("starting pipeline {0}".format(args.stage))

    if args.enable_metrics:
        i = Info(f"os2datascanner_pipeline_{args.stage}", "version number")
        i.info({"version": __version__})
        start_http_server(args.prometheus_port)

    if args.single_cpu:
        available_cpus = sorted(os.sched_getaffinity(0))
        cpu = None
        if (seq_id := os.getenv("SCHEDULE_ON_CPU", None)):
            # If we've been assigned to a specific processor, then use that
            # (modulo the number of actually available CPUs, so we can safely
            # use an instance counter as a processor selector)
            cpu = available_cpus[int(seq_id) % len(available_cpus)]
        else:
            # Otherwise, pick a random CPU to run on
            cpu = random.choice(available_cpus)
        root_logger.info(f"executing only on CPU {cpu}")
        os.sched_setaffinity(0, {cpu})

    if args.profile:
        root_logger.info("enabling profiling")
        profiling.enable_profiling()

    try:
        with SourceManager(width=args.width) as source_manager:
            GenericRunner(
                    source_manager,
                    stage=args.stage,
                    module=module,
                    limit=args.limit).run_consumer()

        if restarting:
            root_logger.info(f"restarting after {args.limit} messages")
            restart_process()
    finally:
        profiling.print_stats(pstats.SortKey.CUMULATIVE, silent=True)


if __name__ == "__main__":
    main()
