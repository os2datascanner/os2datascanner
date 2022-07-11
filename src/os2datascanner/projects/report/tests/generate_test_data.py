import string
import random
from dateutil.tz import gettz
from randomtimestamp import randomtimestamp

from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.dimensions import DimensionsRule
from os2datascanner.engine2.pipeline import messages
from os2datascanner.engine2.model.file import (
        FilesystemHandle, FilesystemSource)
from ..reportapp.management.commands import pipeline_collector
from ..reportapp.utils import hash_handle


def get_different_scan_tag():
    number = random.randint(0, 10)
    return messages.ScanTagFragment(
        scanner=messages.ScannerFragment(
                pk=number,
                name="Dummy test scanner {0}".format(number)),
        time=randomtimestamp(start_year=2020, text=False).replace(tzinfo=gettz()),
        user=None, organisation=None)


def get_different_filesystemhandle(file_ending, folder_level):
    path = '/'
    for _x in range(0, folder_level):
        path += ''.join(random.choice(
            string.ascii_lowercase) for i in range(10)) + '/'
    return FilesystemHandle(
        FilesystemSource("/mnt/fs01.magenta.dk/brugere/af"),
        "{0}{1}{2}".format(path, random.choice(
            string.ascii_lowercase), file_ending)
    )


def get_regex_rule(regex, sensitivity):
    return RegexRule(regex,
                     sensitivity=sensitivity)


def get_common_scan_spec():
    return messages.ScanSpecMessage(
        scan_tag=get_different_scan_tag(),
        source=get_different_filesystemhandle('.txt', 3).source,
        rule=get_regex_rule("Vores hemmelige adgangskode er",
                            Sensitivity.WARNING),
        configuration={},
        filter_rule=None,
        progress=None)


def get_positive_match_with_probability_and_sensitivity():
    return messages.MatchesMessage(
        scan_spec=get_common_scan_spec(),
        handle=get_different_filesystemhandle('.txt', 3),
        matched=True,
        matches=[
            get_matches_with_sensitivity_and_probability(),
            get_dimension_rule_match()
        ])


def get_matches_with_sensitivity_and_probability():
    return messages.MatchFragment(
        rule=get_regex_rule("Vores hemmelige adgangskode er",
                            Sensitivity.CRITICAL),
        matches=[{"dummy": "match object",
                  "probability": 0.6, "sensitivity": 750},
                 {"dummy1": "match object",
                  "probability": 0.0, "sensitivity": 1000},
                 {"dummy2": "match object",
                  "probability": 1.0, "sensitivity": 500}])


def get_dimension_rule_match():
    return messages.MatchFragment(
        rule=DimensionsRule(),
        matches=[{"match": [2496, 3508]}])


def record_match(match):
    """Records a match message to the database as though it were received by
    the report module's pipeline collector."""
    return pipeline_collector.handle_match_message(
            hash_handle(match.handle.to_json_object()),
            match.scan_spec.scan_tag,
            match.to_json_object())


def record_metadata(metadata):
    """Records a metadata message to the database as though it were received by
    the report module's pipeline collector, in the process also creating Alias
    relations."""
    return pipeline_collector.handle_metadata_message(
            hash_handle(metadata.handle.to_json_object()),
            metadata.scan_tag,
            metadata.to_json_object())


def record_problem(problem):
    """Records a problem message to the database as though it were received by
    the report module's pipeline collector. Both Handle- and Source-related
    problems are supported."""
    path = hash_handle(
            problem.handle.to_json_object()
            if problem.handle else problem.source.to_json_object())
    return pipeline_collector.handle_problem_message(
            path, problem.scan_tag, problem.to_json_object())
