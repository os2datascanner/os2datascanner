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

from ...utils import create_alias_and_match_relations
from os2datascanner.projects.report.organizations.models import Alias


def update_match_alias_relations():
    aliases = Alias.objects.all()
    print("Found {0} aliases.".format(aliases.count()))

    approximate_count = 0

    for alias in aliases:
        ac = create_alias_and_match_relations(alias)
        if ac != 0:
            print(f"{alias}: approx. {ac}")
        approximate_count += ac

    print(
            f"Approximately {approximate_count}"
            " DocumentReport/Alias relations created.")


class Command(BaseCommand):
    """Sends emails."""
    help = __doc__

    def handle(self, **options):
        """This command will look for all DocumentReport matches and make
        a relation between the match and the alias if any, and not already
        present.
        """
        update_match_alias_relations()
