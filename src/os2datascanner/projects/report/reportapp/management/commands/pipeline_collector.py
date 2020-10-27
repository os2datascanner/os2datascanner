#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )

from django.core.management.base import BaseCommand

from os2datascanner.utils.system_utilities import json_utf8_decode
from os2datascanner.utils.amqp_connection_manager import start_amqp, \
    set_callback, start_consuming, ack_message
from os2datascanner.engine2.rules.last_modified import LastModifiedRule
from os2datascanner.engine2.pipeline import messages

from ...utils import hash_handle, parse_isoformat_timestamp
from ...models.documentreport_model import DocumentReport


def consume_results(channel, method, properties, body):
    print('Message recieved {} :'.format(body))
    ack_message(method)

    _restructure_and_save_result(body)


def _restructure_and_save_result(result):
    """Method for restructuring and storing result body.

    The agreed structure is as follows:
    {'scan_tag', '2019-11-28T14:56:58', 'matches': null, 'metadata': null,
    'problem': []}
    """
    result = json_utf8_decode(result)
    reference = result.get("handle") or result.get("source")
    tag, queue = _identify_message(result)
    if not reference or not tag or not queue:
        return
    scanner = tag["scanner"]
    time_raw = tag["time"]
    time = parse_isoformat_timestamp(time_raw)

    path = hash_handle(reference)
    prev_entry = DocumentReport.objects.filter(path=path,
            data__scan_tag__scanner=scanner).order_by("-scan_time").first()
    # get_or_create unconditionally writes freshly-created objects to the
    # database (in the version of Django we're using at the moment, at least),
    # so we have to implement similar logic ourselves
    try:
        new_entry = DocumentReport.objects.filter(
                path=path, scan_time=time).get()
    except DocumentReport.DoesNotExist:
        new_entry = DocumentReport(path=path, scan_time=time,
                data={"scan_tag": tag})

    if queue == "matches":
        matches = messages.MatchesMessage.from_json_object(result)
        prev_matches = prev_entry.matches if prev_entry else None

        if prev_entry and prev_entry.resolution_status is None:
            # There are existing unresolved results; resolve them based on the
            # new message
            if prev_matches:
                if not matches.matched:
                    # No new matches. Be cautiously optimistic, but check what
                    # actually happened
                    if (len(matches.matches) == 1
                            and isinstance(matches.matches[0].rule,
                                    LastModifiedRule)):
                        print(reference, "pm !mm lm OT")
                        # The file hasn't been changed, so the matches weren't
                        # actually changed. Instead of making a new entry,
                        # just update the timestamp on the old one
                        prev_entry.scan_time = time
                        prev_entry.save()
                    else:
                        print(reference, "pm !mm ED")
                        # The file has been edited and the matches are no
                        # longer present
                        prev_entry.resolution_status = (
                                DocumentReport.ResolutionChoices.EDITED.value)
                        prev_entry.save()
                else:
                    print(reference, "pm mm ED")
                    # The file has been edited, but matches are still present
                    prev_entry.resolution_status = (
                            DocumentReport.ResolutionChoices.EDITED.value)
                    prev_entry.save()
            else:
                print("!pm")
        else:
            print("!pe.")

        if matches.matched:
            new_entry.data["matches"] = result
            new_entry.save()
    elif queue == "problem":
        problem = messages.ProblemMessage.from_json_object(result)
        if (prev_entry and prev_entry.resolution_status is None
                and problem.missing):
            # The file previously had matches, but has been removed. Resolve
            # them
            print("pr pe RM")
            prev_entry.resolution_status = (
                    DocumentReport.ResolutionChoices.REMOVED.value)
            prev_entry.save()
        else:
            new_entry.data["problem"] = result
            new_entry.save()
    elif queue == "metadata":
        new_entry.data["metadata"] = result
        new_entry.save()


def _identify_message(result):
    origin = result.get('origin')

    if origin == 'os2ds_problems':
        return (result.get("scan_tag"), "problem")
    elif origin == 'os2ds_metadata':
        return (result.get("scan_tag"), "metadata")
    elif origin == "os2ds_matches":
        return (result["scan_spec"].get("scan_tag"), "matches")
    else:
        return None, None



class Command(BaseCommand):
    """Command for starting a pipeline collector process."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--results",
            type=str,
            help="the name of the AMQP queue from which filtered result objects"
                 + " should be read",
            default="os2ds_results")

    def handle(self, results, *args, **options):

        # Start listning on matches queue
        start_amqp(results)
        set_callback(consume_results, results)
        start_consuming()
