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
import os
import logging

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from exchangelib.errors import ErrorNonExistentMailbox
from os2datascanner.engine2.model.ews import EWSAccountSource
from os2datascanner.engine2.model.core import SourceManager
from mptt.models import TreeManyToManyField

from ....organizations.models.aliases import AliasType
from ...utils import upload_path_exchange_users
from .scanner_model import Scanner

logger = logging.getLogger(__name__)


class ExchangeScanner(Scanner):
    """Scanner for Exchange Web Services accounts"""

    userlist = models.FileField(
        null=True,
        blank=True,
        upload_to=upload_path_exchange_users,
    )

    service_endpoint = models.URLField(
        max_length=256,
        verbose_name="Service endpoint",
        blank=True,
        default=""
    )

    org_unit = TreeManyToManyField(
        "organizations.OrganizationalUnit",
        related_name = "exchangescanners",
        blank=True,
        verbose_name=_("organizational unit"),
    )

    def get_userlist_file_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.userlist.name)

    def get_type(self):
        return "exchange"

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return "/exchangescanners/"

    def generate_sources(self):
        user_list = ()
        # org_unit check as you cannot do both simultaneously
        if self.userlist and not self.org_unit:
            user_list = (
                u.decode("utf-8").strip() for u in self.userlist if u.strip()
            )

        # org_unit should only exist if chosen and then be used,
        # but a user_list is allowed to co-exist.
        elif self.org_unit:
            # Create a set so that emails can only occur once.
            user_list = set()
            # loop over all units incl children
            for organizational_unit in self.org_unit.all():
                for unit in organizational_unit.get_descendants(include_self=True):
                    for position in unit.position_set.all():
                        addresses = position.account.aliases.filter(
                            _alias_type=AliasType.EMAIL.value
                        )

                        if not addresses:
                            logger.info(
                                f"user {position.account.username} has no email alias "
                                "connected"
                            )

                        else:
                            for alias in addresses:
                                address = alias.value
                                if address.endswith(self.url):
                                    user_list.add(address.split("@", maxsplit=1)[0])

        for u in user_list:
            logger.info(f"submitting scan for user {u}")
            yield EWSAccountSource(
                domain=self.url.lstrip("@"),
                server=self.service_endpoint or None,
                admin_user=self.authentication.username,
                admin_password=self.authentication.get_password(),
                user=u,
            )

    def verify(self) -> bool:
        for account in self.generate_sources():
            with SourceManager() as sm:
                try:
                    exchangelib_object = sm.open(account)
                    if exchangelib_object.msg_folder_root:
                        logger.info(
                            "OS2datascanner has access to mailbox {0}".format(
                                account.address
                            )
                        )
                except ErrorNonExistentMailbox:
                    logger.info("Mailbox {0} does not exits".format(account.address))
                    return False
        return True
