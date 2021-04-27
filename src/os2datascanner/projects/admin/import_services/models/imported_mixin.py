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
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.

from django.db import models
from django.db.models import F, Q
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


class Imported(models.Model):
    """
    Abstract base class for models that may be imported from external services.

    Instances marked as imported should only be added, modified or
    deleted as instructed by the relevant external service; instances without
    this marking may be modified freely locally.
    """

    imported = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('has been imported'),
    )

    # Store unique ID from external service
    imported_id = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        verbose_name=_('imported unique ID'),
    )
    # Store when last request for import was made
    last_import_requested = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last time an update was requested'),
    )
    # Store when last successful import was made
    last_import = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last successful import'),
    )

    class Meta:
        abstract = True

    @classmethod
    def get_all_awaiting(cls):
        no_request = Q(last_import_requested__isnull=True)
        request_in_future = Q(last_import_requested__gt=now())
        no_import = Q(last_import__isnull=True)
        outdated = Q(last_import__lte=F('last_import_requested'))
        relevant_qs = cls.objects.exclude(no_request | request_in_future)
        return relevant_qs.filter(no_import | outdated)
