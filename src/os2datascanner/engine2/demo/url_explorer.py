#!/usr/bin/env python

"""Summarises an OS2datascanner data source, showing the system's view of
it."""

from sys import stderr
import argparse
import logging
import traceback

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.core import FileResource
from os2datascanner.engine2.model.core import UnknownSchemeError


_loglevels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}


def format_d(depth, fmt, *args, **kwargs):
    return "{0}{1}".format("  " * depth, fmt.format(*args, **kwargs))


def print_source(  # noqa
        manager, source, depth=0, *,
        guess=False, summarise=False, metadata=False, max_depth=None):  # noqa
    try:
        for handle in source.handles(manager):
            print(format_d(depth, "{0}", handle))
            if summarise:
                resource = handle.follow(manager)
                try:
                    if isinstance(resource, FileResource):
                        size = resource.get_size().value
                        mime = resource.compute_type()
                        lm = resource.get_last_modified().value
                        print(format_d(depth + 1, "size {0} bytes", size))
                        print(format_d(depth + 1, "type {0}", mime))
                        print(format_d(depth + 1, "lmod {0}", lm))
                except Exception:
                    print(format_d(depth + 1, "not available"))
            if metadata:
                resource = handle.follow(manager)
                for k, v in resource.get_metadata().items():
                    print(format_d(depth + 1, "metadata:{0} {1}", k, v))
            if max_depth is None or depth < max_depth:
                derived_source = Source.from_handle(
                        handle, manager if not guess else None)
                if derived_source:
                    print_source(
                            manager, derived_source, depth + 1,
                            guess=guess, summarise=summarise,
                            metadata=metadata, max_depth=max_depth)
    except Exception:
        print(format_d(depth, f"{type(source).__name__}: unexpected error:"))
        lines = traceback.format_exc().strip().split("\n")
        for line in lines:
            print(format_d(depth + 1, line))


def add_control_arguments(parser):
    parser.add_argument(
            "--guess-mime",
            action='store_true',
            dest='guess',
            help='Compute the MIME type of each file'
                 ' based on its filename. (default)',
            default=True)
    parser.add_argument(
            "--compute-mime",
            action='store_false',
            dest='guess',
            help='Compute the MIME type of each file based on its content.')
    parser.add_argument(
            "--summarise",
            action='store_true',
            dest='summarise',
            help='Print a brief summary of the content of each file.')
    parser.add_argument(
            "--metadata",
            action='store_true',
            dest='metadata',
            help='Print the metadata associated with each file.')
    parser.add_argument(
            "--max-depth",
            metavar="DEPTH",
            type=int,
            help="Don't recurse deeper than %(metavar)s levels.")


def add_arguments(parser):
    parser.add_argument(
            "urls",
            metavar="URL",
            help="A URL to be explored, for example file:///usr/share/doc or"
                 " https://www.magenta.dk. (Note that not all OS2datascanner"
                 " sources have URL representations.)",
            nargs='+')
    add_control_arguments(parser)
    parser.add_argument(
            "--log-level",
            default="info",
            help="Set the logging level.",
            choices=("critical", "error", "warn", "warning", "info", "debug",)
        )


def main():
    parser = argparse.ArgumentParser()
    add_arguments(parser)

    args = parser.parse_args()

    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    logging.basicConfig(format="%(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("os2datascanner")
    logger.setLevel(_loglevels[args.log_level])

    with SourceManager() as sm:
        for i in args.urls:
            try:
                s = Source.from_url(i)
                if not s:
                    print("{0}: URL parsing failure".format(i), file=stderr)
                else:
                    print_source(
                            sm, s,
                            guess=args.guess,
                            summarise=args.summarise,
                            metadata=args.metadata,
                            max_depth=args.max_depth)
            except UnknownSchemeError:
                print("{0}: unknown URL scheme".format(i), file=stderr)


if __name__ == '__main__':
    main()
