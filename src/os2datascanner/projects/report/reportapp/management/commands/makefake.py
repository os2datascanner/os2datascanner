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

from time import time
from django.core.management.base import BaseCommand
from contextlib import contextmanager

from os2datascanner.utils.system_utilities import time_now
from os2datascanner.engine2.model import http
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.rule import Sensitivity
from os2datascanner.engine2.pipeline import messages
from ...models.organization_model import Organization
from .pipeline_collector import result_message_received_raw


def emit_message(queue, m):
    m = m.to_json_object()
    m["origin"] = queue
    for k in result_message_received_raw(m):
        pass


@contextmanager
def timer(label):
    start = time()
    try:
        yield
    finally:
        duration = time() - start
        print("{0}: finished after {1}s".format(label, duration))


class Command(BaseCommand):
    """Creates realistic (but fake) DocumentReports in the database."""
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain-suffix",
            metavar="NAME",
            default="os2datascanner.invalid",
            help="the domain name under which to create simulated websites"
                    " (default: %(default)s)")
        parser.add_argument(
            "--page-count",
            type=int,
            metavar="NUM",
            default=1000,
            help="the number of pages to scan in each simulated website"
                    " (default: %(default)d)")
        parser.add_argument(
            "--match-fraction",
            type=float,
            metavar="FRAC",
            default=1.0,
            help="the fraction of simulated pages in which a match should"
                    " be reported (default: %(default)#.1f)")
        parser.add_argument(
            "--match-count",
            type=int,
            metavar="NUM",
            default=10,
            help="the number of matches to find on each simulated page with"
                    " matches (default: %(default)d)")
        parser.add_argument(
            "--site-count",
            required=True,
            type=int,
            metavar="NUM",
            default=10,
            help="simulate the results of scanning %(metavar)s websites"
                    " (sensible: 10, database stress test: 100)")

    def handle(self, *, domain_suffix, page_count, match_fraction, match_count,
            site_count, **options):
        clamped_frac = 1.0 - max(0.0, min(1.0, match_fraction))
        match_from = page_count * clamped_frac

        organization = Organization.objects.first()
        scan_tag = messages.ScanTagFragment(
                time=time_now(),
                user="dummy",
                scanner=messages.ScannerFragment(pk=0, name="Dummy scan"),
                organisation=messages.OrganisationFragment(
                        name=organization.name, uuid=organization.uuid))
        rule = CPRRule(sensitivity=Sensitivity.CRITICAL)
        scan_specification = messages.ScanSpecMessage(
                scan_tag=scan_tag,
                source=None,  # placeholder
                rule=rule,
                configuration={},
                progress=None)

        for site in range(0, site_count):
            site_domain = "{0}.{1}".format(site, domain_suffix)

            with timer(site_domain):
                site_source = http.WebSource(url="https://" + site_domain)
                site_spec = scan_specification._replace(source=site_source)

                for page in range(0, page_count):
                    page_handle = http.WebHandle(site_source,
                            "{0}.html".format(page))
                    match_here = messages.MatchesMessage(
                            scan_spec=site_spec,
                            handle=page_handle,
                            matched=False,
                            matches=[])
                    matched = (page >= match_from)
                    if matched:
                        fragment = messages.MatchFragment(
                                rule,
                                [
                                    {
                                        "offset": match * 100,
                                        "match": "0101XX-XXXX",
                                        "context": "blah blah blah 0101XX-XXXX"
                                                " blah blah blah",
                                        "context_offset": 15,
                                        "probability": 1.0
                                    }
                                for match in range(1, match_count + 1)])
                        match_here = match_here._replace(
                                matched=True, matches=[fragment])
                        emit_message("os2ds_metadata",
                                messages.MetadataMessage(
                                        scan_tag=scan_tag,
                                        handle=page_handle,
                                        metadata={
                                            "web-domain": site_domain
                                        }))
                    emit_message("os2ds_matches", match_here)
