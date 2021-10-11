#!/usr/bin/env python

from sys import stderr
import argparse
import logging

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.core import FileResource
from os2datascanner.engine2.model.core import UnknownSchemeError

"""Explore an url and see what datascanner understands(with `--summarise`)

url can be one of the scheme-types supported by datascanner. Schemes `file:` and
`http:` are probably the easiet to use. The urls have to point to a "directory" not a
specific resource.
Note: The `file` url have to be absolute (i.e. no `~/` or use file:`readlink -f ~/`)

Example:
python -m os2datascanner.engine2.demo.url_explorer file:/home/User/Downloads
python -m os2datascanner.engine2.demo.url_explorer file:`readlink -f ~/Downloads`
python -m os2datascanner.engine2.demo.url_explorer https://www.magenta.dk

Supported urls can be found by:

from os2datascanner.engine2.model.core import Source
Source._Source__url_handlers
"""


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

def print_source(manager, source, depth=0, *,
        guess=False, summarise=False, max_depth=None):
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
        if max_depth is None or depth < max_depth:
            derived_source = Source.from_handle(
                    handle, manager if not guess else None)
            if derived_source:
                print_source(manager, derived_source, depth + 1,
                        guess=guess, summarise=summarise, max_depth=max_depth)


def add_arguments(parser):
    parser.add_argument(
            "urls",
            metavar="URL",
            help='A URL to be explored. ' +
            'Examples: file:`readlink -f ~/Downloads` OR https://magenta.dk. ' +
            'The URL have to start with the scheme and be absolute! ' +
            'Read the header of this file for more info.',
            nargs='+')
    parser.add_argument(
            "--guess-mime",
            action='store_true',
            dest='guess',
            help='Compute the MIME type of each file' +
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
            "--max-depth",
            metavar="DEPTH",
            type=int,
            help="Don't recurse deeper than %(metavar)s levels.")
    parser.add_argument(
            "--log-level",
            default="info",
            help=("Set logging level. Example --log-level=debug', default='info'"),
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
                    print_source(sm, s,
                            guess=args.guess,
                            summarise=args.summarise,
                            max_depth=args.max_depth)
            except UnknownSchemeError as ex:
                print("{0}: unknown URL scheme".format(i), file=stderr)

if __name__ == '__main__':
    main()
