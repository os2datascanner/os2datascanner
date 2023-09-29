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
import termplotlib as tpl

from django.core.management.base import BaseCommand
from django.db.models import Count, F
from django.db.models.functions import Lower

from ....organizations.models import Account, Alias, OrganizationalUnit, Organization
from ...models.documentreport import DocumentReport


class Command(BaseCommand):
    """Run diagnostics on the report module."""

    help = __doc__

    choice_list = ["Account", "Alias", "DocumentReport", "OrganizationalUnit",
                   "Organization", "Problem"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            default=False,
            choices=self.choice_list,
            nargs="+",
            help="Only run diagnostics on a specific part of the report module.")

    def diagnose_accounts(self):
        print("\n\n>> Running diagnostics on accounts ...")
        accounts = Account.objects.all()
        accounts_without_username = accounts.filter(username="").values("pk")
        accounts_without_user = accounts.filter(user__isnull=True).values("username", "pk")
        username_counts = accounts.annotate(username_lower=Lower("username")
                                            ).values("username_lower").order_by(
        ).annotate(count=Count("username_lower")).order_by("-count").filter(count__gte=2)

        print(f"Found a total of {accounts.count()} accounts.")

        if accounts_without_username:
            print(f"Found {len(accounts_without_username)} accounts without a username:", ", ".join(
                [d["pk"] for d in accounts_without_username]))

        if accounts_without_user:
            print(f"Found {len(accounts_without_user)} accounts without a user:", ", ".join(
                [f'''{d['username']} ({d['pk']})''' for d in accounts_without_user]))

        if username_counts:
            print(f"Found {len(username_counts)} cases of duplicate usernames "
                  "(disregarding case):", ", ".join(
                      [f"{d['username_lower']} ({d['count']})" for d in username_counts]))

    def diagnose_aliases(self):
        print("\n\n>> Running diagnostics on aliases ...")
        aliases = Alias.objects.all()
        alias_types = aliases.values(
            "_alias_type").order_by().annotate(count=Count("_alias_type"))
        # We have to make new querysets here, as annotating with Count
        # Will always give "0" if the counted field is null.
        aliases_with_no_user = aliases.filter(user__isnull=True).values("pk")
        aliases_with_no_account = aliases.filter(account__isnull=True).values("pk")

        nl = '\n  '
        print(
            f"Found a total of {aliases.count()} aliases: \n  "
            f"{nl.join([f'''{a['_alias_type']}: {a['count']}''' for a in alias_types])}")

        if aliases_with_no_user:
            print(f"Found {len(aliases_with_no_user)} aliases with no user:",
                  ", ".join([d['pk'] for d in aliases_with_no_user]))

        if aliases_with_no_account:
            print(f"Found {len(aliases_with_no_account)} aliases with no account:",
                  ", ".join([d['pk'] for d in aliases_with_no_account]))

    def diagnose_problems(self):
        print("\n\n>> Running diagnostics on problems ...")
        all_problems = DocumentReport.objects.filter(raw_problem__isnull=False)
        problems = all_problems.values("raw_problem__message").order_by().annotate(
            count=Count("raw_problem__message")).order_by("-count")

        if problems:
            print(
                f"Found {len(problems)} different problems ({all_problems.count()} "
                "problems in total). Now presenting the 5 most common:")

            for message_dict in problems[:5]:
                print(
                    f"  ({message_dict['count']} counts) {message_dict['raw_problem__message']}")

    def diagnose_reports(self):
        print("\n\n>> Running diagnostics on reports ...")
        reports = DocumentReport.objects.all()
        matches = reports.filter(number_of_matches__gte=1)
        handled = matches.filter(
            resolution_status__isnull=False).values("resolution_status").order_by().annotate(
            count=Count("resolution_status")).order_by("-count")
        unhandled = matches.filter(resolution_status__isnull=True)
        scannerjobs = matches.values(
            "scanner_job_pk", "scanner_job_name").order_by().annotate(
            count=Count("pk")).order_by("-count")

        print(f"Found {reports.count()} reports in total, {matches.count()} of which "
              f"contain matches, {unhandled.count()} of which are unhandled.")

        if handled:
            print("\nMatches are handled in the following way:")
            labels = [
                DocumentReport.ResolutionChoices(
                    res_dict['resolution_status']).label for res_dict in handled]
            counts = [res_dict['count'] for res_dict in handled]
            # Create figure in the terminal
            fig = tpl.figure()
            fig.barh(counts, labels)
            fig.show()

        if matches:
            print("\nMatches come from the following scannerjobs:")
            labels = [
                f"{scannerjob['scanner_job_name']} ({scannerjob['scanner_job_pk']})"
                for scannerjob in scannerjobs]
            counts = [scannerjob['count'] for scannerjob in scannerjobs]

            # Create figure in the terminal
            fig = tpl.figure()
            fig.barh(counts, labels)
            fig.show()

        # Check for timestamps
        no_created_timestamp = reports.filter(created_timestamp__isnull=True)
        no_resolution_time = reports.filter(
            resolution_status__isnull=False, resolution_time__isnull=True)
        no_both_timestamps = no_created_timestamp & no_resolution_time

        if no_created_timestamp.count():
            print(f"Found {no_created_timestamp.count()} reports without a 'created_timestamp'.")
        if no_resolution_time.count():
            print(f"Found {no_resolution_time.count()} handled reports without"
                  f" a 'resolution_time'.")
        if no_both_timestamps.count():
            print(
                f"Found {no_both_timestamps.count()} handled reports without "
                f"both a 'created_timestamp' and a 'resolution_time'.")

        # Check for reports handled before they were created
        impossible_timestamps = reports.filter(
            resolution_status__isnull=False,
            created_timestamp__gt=F("resolution_time"))

        if impossible_timestamps.count():
            print(
                f"Found {impossible_timestamps.count()} handled reports, where"
                f" the 'resolution_time' is earlier than the 'created_timestamp'.")

        # Check for remediator reports
        remediator_matches = matches.filter(alias_relation__isnull=True)

        if remediator_matches.count():
            print(f"Found {remediator_matches.count()} matched reports "
                  "delegated to a remediator.")

        # Top five matched accounts
        account_matches = matches.values("alias_relation__account__username").order_by(
            ).annotate(count=Count("alias_relation__account__username")).order_by("-count")

        if account_matches:
            print("\nPresenting the five accounts with most matched reports:")
            nl = '\n  '
            print(" ", nl.join(
                [f"{acc['alias_relation__account__username']}: {acc['count']} "
                 "matched reports" for acc in account_matches[:5] if acc['count']]))

    def diagnose_units(self):
        print("\n\n>> Running diagnostics on units ...")
        units = OrganizationalUnit.objects.count()

        print(f"Found {units} units.")

    def diagnose_organizations(self):
        print("\n\n>> Running diagnostics on organizations ...")
        orgs = Organization.objects.values("pk", "name", "email_notification_schedule")

        print(f"Found {len(orgs)} organizations.")

        if os2 := orgs.filter(name="OS2datascanner").first():
            print(
                f"The organization with UUID {os2['pk']} is called 'OS2datascanner'."
                " Should this be changed?'")

        for org in orgs:
            print(
                f"  Notification schedule for {org['name']}: {org['email_notification_schedule']}")

    def handle(self, only, **options):

        if not only:
            only = self.choice_list

        for opt in only:
            match opt:
                case "Account":
                    self.diagnose_accounts()
                case "Alias":
                    self.diagnose_aliases()
                case "Problem":
                    self.diagnose_problems()
                case "DocumentReport":
                    self.diagnose_reports()
                case "OrganizationalUnit":
                    self.diagnose_units()
                case "Organization":
                    self.diagnose_organizations()
