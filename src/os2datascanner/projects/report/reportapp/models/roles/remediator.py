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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

from django.utils.translation import gettext_lazy as _
from .role import Role


class Remediator(Role):
    """The Remediator role's filter accepts all matches that have not already
    been resolved and whose metadata cannot be mapped to an existing system
    user."""

    def filter(self, document_reports):
        # XXX: this logic only makes sense if all system users belong to the
        # same organisation

        return document_reports.filter(alias_relation__isnull=True)

    class Meta:
        verbose_name = _("remediator")
        verbose_name_plural = _("remediators")
