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

from ...utils import hash_handle
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
    updated_fields = _format_results(result)
    if updated_fields:
        reference = result.get('handle') or result.get('source')

        report_obj, is_created = DocumentReport.objects.get_or_create(
            path=hash_handle(reference))

        if is_created:
            # if created updatde_fields are stored.
            report_obj.data = updated_fields
        else:
            # else merge the new message with the existing report_obj.data
            report_obj.data['scan_tag'] = updated_fields['scan_tag']
            if updated_fields.get('matches'):
                report_obj.data['matches'] = updated_fields.get('matches')
            elif updated_fields.get('metadata'):
                report_obj.data['metadata'] = updated_fields.get('metadata')

        report_obj.save()

def _format_results(result):
    """Method for restructuring result body"""
    updated_fields = {}

    origin = result.get('origin')

    if origin == 'os2ds_problems':
        updated_fields['scan_tag'] = result.get('scan_tag')
        updated_fields['problem'] = result
    elif origin == 'os2ds_metadata':
        updated_fields['scan_tag'] = result.get('scan_tag')
        updated_fields['metadata'] = result
    elif origin == 'os2ds_matches':
        if result.get('matched'):
            updated_fields['scan_tag'] = result.get('scan_spec').get('scan_tag')
            updated_fields['matches'] = result
        else:
            print('Object processed with no matches: {}'.format(result))

    return updated_fields



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
