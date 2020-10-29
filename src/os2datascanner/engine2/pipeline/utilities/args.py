import argparse


def make_common_argument_parser():
    parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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

    return parser


def make_sourcemanager_configuration_block(parser):
    configuration = parser.add_argument_group("configuration")
    configuration.add_argument(
            "--width",
            type=int,
            metavar="SIZE",
            help="allow each source to have at most %(metavar) "
                    "simultaneous open sub-sources",
            default=3)

    return configuration
