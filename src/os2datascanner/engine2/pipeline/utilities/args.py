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


class AppendReplaceAction(argparse.Action):
    """AppendReplaceAction behaves like the 'append' action, but the default
    value, if there is one, will be removed from the list the first time a
    value is explicitly specified."""
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        self._fired = set()
        default = kwargs.get("default")
        if default and not isinstance(default, list):
            kwargs["default"] = [default]
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if not id(namespace) in self._fired:
            setattr(namespace, self.dest, [])
            self._fired.add(id(namespace))
        setattr(namespace, self.dest, getattr(namespace, self.dest) + [values])
