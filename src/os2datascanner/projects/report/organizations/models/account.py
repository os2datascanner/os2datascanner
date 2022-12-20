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
#
import os
import logging

from PIL import Image
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User

from os2datascanner.core_organizational_structure.models import Account as Core_Account
from os2datascanner.utils.system_utilities import time_now
from rest_framework import serializers

from ..serializer import BaseSerializer

logger = logging.getLogger(__name__)


class StatusChoices(models.IntegerChoices):
    GOOD = 0, _("Completed")
    OK = 1, _("Accepted")
    BAD = 2, _("Not accepted")


class Account(Core_Account):
    """ Core logic lives in the core_organizational_structure app.
    Additional logic can be implemented here, but currently, none needed, hence we pass. """

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='account',
        verbose_name=_('User'),
        null=True, blank=True)
    last_handle = models.DateTimeField(
        verbose_name=_('Last handle'),
        null=True,
        blank=True)
    _image = models.ImageField(
        upload_to="media/images",
        default=None,
        null=True,
        blank=True,
        verbose_name=_('image'))
    match_count = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name=_("Number of matches"))
    match_status = models.IntegerField(
        choices=StatusChoices.choices,
        default=1,
        null=True,
        blank=True)

    def update_last_handle(self):
        self.last_handle = time_now()
        self.save()

    @property
    def time_since_last_handle(self):
        """Return time since last handled, if the user has handled something.
        If not, return 3 days to trigger a warning to the user."""
        return (time_now() - self.last_handle).total_seconds() if self.last_handle else 60*60*24*3

    @property
    def image(self):
        return os.path.join(settings.MEDIA_ROOT, self._image.url) if self._image else None

    @property
    def status(self):
        return StatusChoices(self.match_status).label

    def _count_matches(self):
        """Counts the number of matches associated with the account."""
        count = 0
        for alias in self.aliases.all():
            count += alias.match_relation.filter(
                resolution_status__isnull=True,
                raw_matches__matched=True,
                only_notify_superadmin=False).count()
        self.match_count = count

    def _calculate_status(self):
        """Calculate the status of the user. The user can have one of three
        statuses: GOOD, OK and BAD. The status is calulated on the basis of
        the number of matches associated with the user, and how often the user
        has handled matches recently."""

        matches_by_week = self.count_matches_by_week(weeks=3)

        total_new = 0
        total_handled = 0
        for week_obj in matches_by_week:
            total_new += week_obj["new"]
            total_handled += week_obj["handled"]

        if matches_by_week[0]["matches"] == 0:
            self.match_status = StatusChoices.GOOD
        elif total_handled == 0 or total_handled/total_new < 0.75:
            self.match_status = StatusChoices.BAD
        else:
            self.match_status = StatusChoices.OK

    def count_matches_by_week(self, weeks: int = 52):  # noqa CCR001

        # This is placed here to avoid circular import
        from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport

        all_matches = list(DocumentReport.objects.filter(
            raw_matches__matched=True,
            alias_relation__account=self,
            only_notify_superadmin=False))

        next_monday = timezone.now() + timedelta(weeks=1) - timedelta(
                days=timezone.now().weekday(),
                hours=timezone.now().hour,
                minutes=timezone.now().minute,
                seconds=timezone.now().second)

        matches_by_week = []

        for i in range(weeks):
            begin_monday = next_monday - timedelta(weeks=i+1)
            end_monday = next_monday - timedelta(weeks=i)

            matches_by_end = 0
            new_matches = 0
            handled_matches = 0
            for match in all_matches:
                if match.created_timestamp <= end_monday and (
                            match.resolution_time is None
                        or match.resolution_time >= end_monday):
                    matches_by_end += 1
                if match.created_timestamp <= end_monday \
                        and match.created_timestamp >= begin_monday:
                    new_matches += 1
                if match.resolution_time and match.resolution_time <= end_monday \
                        and match.resolution_time >= begin_monday:
                    handled_matches += 1

            matches_by_week.append({
                "weeknum": begin_monday.isocalendar().week,
                "matches": matches_by_end,
                "new": new_matches,
                "handled": handled_matches,
            })

        return matches_by_week

    def save(self, *args, **kwargs):

        self._count_matches()
        self._calculate_status()

        super().save(*args, **kwargs)


@receiver(post_save, sender=Account)
def resize_image(sender, **kwargs):
    size = (300, 300)
    try:
        with Image.open(kwargs["instance"]._image.path) as image:
            image.thumbnail(size, Image.ANTIALIAS)
            image.save(kwargs["instance"]._image.path, optimize=True)
    except ValueError:
        logger.debug("image resize failed", exc_info=True)


class AccountSerializer(BaseSerializer):
    class Meta:
        model = Account
        fields = '__all__'

    # This field has to be redefined here, cause it is read-only on model.
    uuid = serializers.UUIDField()
