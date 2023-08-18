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
from django.db.models import Count

from ....organizations.models import Account, Alias, OrganizationalUnit, Organization
from ...models.usererrorlog import UserErrorLog
from ...models.rules.rule import Rule


class Command(BaseCommand):
    """Run diagnostics on the admin module."""

    help = __doc__

    choice_list = ["Account", "Alias", "UserErrorLog", "OrganizationalUnit",
                   "Organization", "Rule"]

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            default=False,
            choices=self.choice_list,
            nargs="+",
            help="Only run diagnostics on a specific part of the admin module.")

    def diagnose_accounts(self):
        print("\n\n>> Running diagnostics on accounts ...")
        accounts = Account.objects.all()
        accounts_without_username = accounts.filter(username="").values("pk")

        print(f"Found a total of {accounts.count()} accounts.")

        if accounts_without_username:
            print(f"Found {len(accounts_without_username)} accounts without a username:", ", ".join(
                [d["pk"] for d in accounts_without_username]))

    def diagnose_aliases(self):
        print("\n\n>> Running diagnostics on aliases ...")
        aliases = Alias.objects.all()
        alias_types = aliases.values(
            "_alias_type").order_by().annotate(count=Count("_alias_type"))
        aliases_with_no_account = aliases.filter(account__isnull=True).values("pk")

        nl = '\n  '
        print(
            f"Found a total of {aliases.count()} aliases: \n  "
            f"{nl.join([f'''{a['_alias_type']}: {a['count']}''' for a in alias_types])}")

        if aliases_with_no_account:
            print(f"Found {len(aliases_with_no_account)} aliases with no account:",
                  ", ".join([d['pk'] for d in aliases_with_no_account]))

    def diagnose_errors(self):
        print("\n\n>> Running diagnostics on errors ...")
        all_errors = UserErrorLog.objects.all()
        errors = all_errors.values("error_message").order_by().annotate(
            count=Count("error_message")).order_by("-count")

        if errors.exists():
            print(
                f"Found {errors.count()} different errors ({all_errors.count()} "
                "errors in total). Now presenting the 5 most common:")

            for message_dict in errors[:5]:
                print(
                    f"  ({message_dict['count']} counts) {message_dict['error_message']}")

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

    def diagnose_rules(self):
        print("\n\n>> Running diagnostics on rules ...")
        rules = Rule.objects.all().select_related('customrule')

        print(f"Found {rules.count()} rules:")
        for rule in rules:
            print(f"  {rule.name} ({rule.__class__})")

    def handle(self, only, **options):

        if not only:
            only = self.choice_list

        if "Account" in only:
            self.diagnose_accounts()

        if "Alias" in only:
            self.diagnose_aliases()

        if "UserErrorLog" in only:
            self.diagnose_errors()

        if "OrganizationalUnit" in only:
            self.diagnose_units()

        if "Organization" in only:
            self.diagnose_organizations()

        if "Rule" in only:
            self.diagnose_rules()
