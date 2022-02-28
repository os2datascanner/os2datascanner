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
from django.db.models import Q

from os2datascanner.projects.report.reportapp.models.aliases.webdomainalias_model import WebDomainAlias  # noqa: E501

from ...models.aliases.adsidalias_model import ADSIDAlias
from ...models.aliases.alias_model import Alias
from ...models.documentreport_model import DocumentReport
from ...models.aliases.emailalias_model import EmailAlias


def update_match_alias_relations():
    matches = DocumentReport.objects.filter(
        Q(raw_matches__matched=True))
    print("Found {0} matches.".format(matches.count()))
    aliases = Alias.objects.all()
    print("Found {0} aliases.".format(aliases.count()))
    for alias in aliases:
        try:
            tm = Alias.match_relation.through

            if EmailAlias.objects.filter(pk=alias.pk):
                subAlias = EmailAlias.objects.get(pk=alias.pk)
                reports = matches.filter(raw_metadata__metadata__contains={
                    str('email-account'): str(subAlias.address)})
                tm.objects.bulk_create(
                    [tm(documentreport_id=r.pk, alias_id=alias.pk) for r in
                     reports], ignore_conflicts=True)
                print("Approx. {0} EmailAlias' relation created.".format(
                    len(reports)))
            elif WebDomainAlias.objects.filter(pk=alias.pk):
                subAlias = WebDomainAlias.objects.get(pk=alias.pk)
                reports = matches.filter(raw_metadata__metadata__contains={
                    str('web-domain'): str(subAlias.domain)})
                tm.objects.bulk_create(
                    [tm(documentreport_id=r.pk, alias_id=alias.pk) for r in
                     reports], ignore_conflicts=True)
                print("Approx. {0} WebDomainAlias' relation created.".format(
                    len(reports)))
            elif ADSIDAlias.objects.filter(pk=alias.pk):
                subAlias = ADSIDAlias.objects.get(pk=alias.pk)
                reports = matches.filter(raw_metadata__metadata__contains={
                    str('filesystem-owner-sid'): str(subAlias.sid)})
                tm.objects.bulk_create(
                    [tm(documentreport_id=r.pk, alias_id=alias.pk) for r in
                     reports], ignore_conflicts=True)
                print("Approx. {0} ADSIDAlias' relation created.".format(
                    len(reports)))
        except Exception:
            print("no subAlias")


class Command(BaseCommand):
    """Sends emails."""
    help = __doc__

    def handle(self, **options):
        """This command will look for all DocumentReport matches and make
        a relation between the match and the alias if any, and not already
        present.
        """
        update_match_alias_relations()
