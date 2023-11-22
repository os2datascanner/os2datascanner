"""Prints YAML or JSON summaries of Django database objects."""

# XXX: The true (project-relative) path of this file is src/os2datascanner/
# projects/utils/print_objects.py; the administration system and report module
# reference it by relative symbolic links. Don't edit it through the symbolic
# links, as that might break them!

from ast import literal_eval
import sys
import json
import uuid
import yaml
from functools import partial

import argparse
from django.apps import apps
from django.db import models
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand


model_mapping = {model.__name__: model for model in apps.get_models()}


def model_class(model):
    """Given the simple name of a registered Django model class, returns that
    class."""
    if model in model_mapping:
        return model_mapping[model]
    else:
        raise argparse.ArgumentTypeError(
                "'{0}': Model class not known".format(model))


def parse_fl_string(flt):
    """Transforms a string representing a Django filter expression (for
    example, ['scanner__pk=20', 'owner__username__icontains="af@"']) into a
    dict that can be used as keyword arguments to a function requiring a field
    lookup.

    The right hand side of the expression can have several forms:

    * "F:" followed by an expression will become a Django F() object;
    * "Count:" followed by an expression will become a Django Count() object;
    * a Python literal will be parsed (as though by ast.literal_eval) to an
      appropriately typed value; and
    * anything else will be treated as a string literal."""
    lhs, rhs = flt.split("=", maxsplit=1)
    try:
        rhs = literal_eval(rhs)
    except (ValueError, SyntaxError,):
        if ":" in rhs:
            match rhs.split(":", maxsplit=1):
                case ("Count", field_expr):
                    rhs = models.Count(field_expr)
                case ("F", field_expr):
                    rhs = models.F(field_expr)
                case (mystery, _):
                    raise ValueError(
                            f"operator {mystery} was not understood")
        else:
            # Do nothing; just leave rhs as a string
            pass
    return lhs, rhs


class CollectorActionFactory:
    class Action(argparse.Action):
        def __init__(self, *args, caf_list, caf_prefix, **kwargs):
            super().__init__(*args, **kwargs)
            self.caf_list = caf_list
            self.caf_prefix = list(caf_prefix)

        def __call__(self, parser, namespace, values, option_string):
            if getattr(namespace, self.dest, None) is None:
                setattr(namespace, self.dest, [])
            getattr(namespace, self.dest).append(self.caf_prefix + [values])

    def __init__(self):
        self.list = []

    def make_collector_action(self, *prefix):
        return partial(
                CollectorActionFactory.Action,
                caf_list=self.list, caf_prefix=prefix)


def get_possible_fields(qs) -> list[str]:
    # Trivially adapted from django.db.models.sql.query.Query.names_to_path
    return sorted([
            *models.sql.query.get_field_names_from_opts(qs.model._meta),
            *qs.query.annotation_select,
            *qs.query._filtered_relations])


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        caf = CollectorActionFactory()

        parser.add_argument(
            '--exclude',
            dest="filt_ops",
            metavar="FL",
            type=str,
            action=caf.make_collector_action("exclude"),
            help="a Django field lookup to exclude objects")
        parser.add_argument(
            '--filter',
            dest="filt_ops",
            metavar="FL",
            type=str,
            action=caf.make_collector_action("filter"),
            help="a Django field lookup to filter objects")

        parser.add_argument(
            '--field',
            dest="fields",
            metavar="NAME",
            type=str,
            action="append",
            help="a Django field name to include in the output (can be used"
                 " multiple times; if not used, all fields are included)")
        parser.add_argument(
            '--annotate',
            dest="filt_ops",
            metavar="FL",
            type=str,
            action=caf.make_collector_action("annotate"),
            help="a Django field lookup describing an annotation to add to the"
                 " query set")

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--order-by',
            type=str,
            metavar="EXPR",
            action="store",
            help="the Django field (expression) to order the results by"
                 " (ascending)")
        group.add_argument(
            '--order-by-desc',
            type=str,
            metavar="EXPR",
            action="store",
            default="pk",
            help="the Django field (expression) to order the results by"
                 " (descending)")

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '--limit',
            type=int,
            metavar="COUNT",
            action="store",
            default=10,
            help="the number of results to collect for printing")
        group.add_argument(
            '--no-limit',
            action="store_const",
            const=None,
            dest="limit",
            help="collect all results for printing")

        parser.add_argument(
            '--offset',
            type=int,
            action="store",
            default=None,
            help="the offset at which to start to collect results")
        parser.add_argument(
            '--with-sql',
            action="store_true",
            help="also print the computed SQL statement for the query")
        parser.add_argument(
            '--json',
            dest="format",
            action="store_const",
            const="json",
            default="yaml",
            help="output results as JSON, not YAML")
        parser.add_argument(
            'model',
            type=model_class,
            help='a Django model class',
        )

        parser.epilog = (
                """Simple Django field lookups with a Python literal
                ('scanner_pk=20', 'account__username__icontains="af@"')
                are supported, but for convenience you can also omit quotation
                marks around string values ("name__icontains=bestyrelse") or
                use a special colon-separated prefix to invoke a Django
                aggregation or query function
                ("match_count=Count:match_relation",
                "username=F:account__username").')""")

    def handle(  # noqa CCR001
            self, *,
            order_by, order_by_desc, limit, offset, model, fields,
            filt_ops, with_sql, format, **kwargs):
        manager = model.objects

        if hasattr(manager, "select_subclasses"):
            queryset = manager.select_subclasses().all()
        else:
            queryset = manager.all()

        for verb, fexpr in (filt_ops or ()):
            lhs, rhs = parse_fl_string(fexpr)
            try:
                match verb:
                    case "filter":
                        queryset = queryset.filter(**{lhs: rhs})
                    case "exclude":
                        queryset = queryset.exclude(**{lhs: rhs})
                    case "annotate":
                        queryset = queryset.annotate(**{lhs: rhs})
            except FieldError:
                print(
                        f"""Django didn't like the field lookup "{lhs}"."""
                        " Valid fields at this point are:", file=sys.stderr)
                for field in get_possible_fields(queryset):
                    print(f"\t{field}", file=sys.stderr)
                sys.exit(2)

        queryset = queryset.order_by(
                order_by
                if order_by is not None
                else f"-{order_by_desc}")

        queryset = queryset.values(*(fields or []))

        if (limit, offset) != (None, None):
            queryset = queryset[slice(offset, (offset or 0) + limit)]

        if with_sql:
            print(queryset.query)

        queryset = list(queryset)
        # Lightly postprocess the results: obscure passwords and prevent
        # UUIDField objects from being dumped in their unhelpful raw form
        for obj in queryset:
            for key, value in obj.items():
                if "password" in key and isinstance(value, str):
                    obj[key] = "█" * min(len(value), 8)
                elif isinstance(value, uuid.UUID):
                    obj[key] = repr(value)

        if format == "json":
            representation = json.dumps(
                    queryset, ensure_ascii=False, default=repr,
                    indent=True)
        else:
            representation = yaml.safe_dump(
                    queryset, allow_unicode=True)
        print(representation.rstrip())
