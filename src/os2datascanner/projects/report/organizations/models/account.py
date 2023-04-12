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
from rest_framework import serializers
from rest_framework.fields import UUIDField
from django.conf import settings
from django.db.models import Count
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_delete

from os2datascanner.core_organizational_structure.models import Account as Core_Account
from os2datascanner.core_organizational_structure.models import \
    AccountSerializer as Core_AccountSerializer
from os2datascanner.core_organizational_structure.models.organization import LeaderPageConfigChoices
from os2datascanner.utils.system_utilities import time_now

from ..seralizer import BaseBulkSerializer, SelfRelatingField

logger = logging.getLogger(__name__)


class StatusChoices(models.IntegerChoices):
    GOOD = 0, _("Completed")
    OK = 1, _("Accepted")
    BAD = 2, _("Not accepted")


class AccountManager(models.Manager):
    """ Account and User models come as a pair. AccountManager takes on the responsibility
    of creating User objects when Accounts are created.
    Unique to the report module.
    """

    # TODO: Out-phase User in favor of Account
    # This is because User and Account co-exist, but a User doesn't have any unique identifier
    # that makes sense from an Account..
    # This means that we risk creating multiple User objects, if users username attribute changes.
    # It's the best we can do for now, until we out-phase User objects entirely
    def create(self, **kwargs):
        user_obj, created = User.objects.update_or_create(
            username=kwargs.get("username"),
            defaults={
                "first_name": kwargs.get("first_name") or '',
                "last_name": kwargs.get("last_name") or ''
            })
        account = Account(**kwargs, user=user_obj)
        account.save()

        return account

    # We must also delete the User object.
    def delete(self, *args, **kwargs):
        self.user.delete()
        return super().delete(*args, **kwargs)

    def bulk_create(self, objs, **kwargs):
        for account in objs:
            user_obj, created = User.objects.update_or_create(
                username=account.username,
                defaults={
                    "first_name": account.first_name or '',
                    "last_name": account.last_name or ''
                })
            account.user = user_obj
        return super().bulk_create(objs, **kwargs)

    def bulk_update(self, objs, fields, **kwargs):
        if any(field in ("username", "first_name", "last_name",) for field in fields):
            for account in objs:
                user: User = account.user
                user.username = account.username
                user.first_name = account.first_name or ''
                user.last_name = account.last_name or ''
                user.save()
        return super().bulk_update(objs, fields, **kwargs)


class Account(Core_Account):
    """ Core logic lives in the core_organizational_structure app.
    Additional logic can be implemented here """

    serializer_class = None
    # Sets objects manager for Account
    objects = AccountManager()

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
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
    withheld_matches = models.IntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name=_("Number of withheld matches"))
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
        """Counts the number of unhandled matches associated with the account."""
        from ...reportapp.models.documentreport import DocumentReport
        reports = DocumentReport.objects.filter(
            alias_relation__account=self,
            number_of_matches__gte=1,
            resolution_status__isnull=True).values(
                "only_notify_superadmin").order_by(
                    "only_notify_superadmin").annotate(
            count=Count("only_notify_superadmin")).values(
            "only_notify_superadmin",
            "count")

        # TODO: Revisit logic below (and its tests, organizations/tests/test_accounts.py)
        self.match_count = 0
        self.withheld_matches = 0
        for obj in reports:
            if obj.get("only_notify_superadmin"):
                self.withheld_matches = obj.get("count")
            else:
                self.match_count = obj.get("count")

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
        elif total_handled == 0 or total_new != 0 and total_handled/total_new < 0.75:
            self.match_status = StatusChoices.BAD
        else:
            self.match_status = StatusChoices.OK

    def count_matches_by_week(self, weeks: int = 52):  # noqa: CCR001

        # This is placed here to avoid circular import
        from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport

        all_matches = DocumentReport.objects.filter(
                number_of_matches__gte=1,
                alias_relation__account=self,
                only_notify_superadmin=False).values("created_timestamp", "resolution_time")

        next_monday = timezone.now() + timedelta(weeks=1) - timedelta(
                days=timezone.now().weekday(),
                hours=timezone.now().hour,
                minutes=timezone.now().minute,
                seconds=timezone.now().second)

        matches_by_week = [
            {
                "begin_monday": next_monday - timedelta(weeks=i+1),
                "end_monday": next_monday - timedelta(weeks=i),
                "weeknum": (next_monday - timedelta(weeks=i+1)).isocalendar().week,
                "matches": 0,
                "new": 0,
                "handled": 0
            } for i in range(weeks)
        ]

        for report in all_matches:
            # Set temporary timestamps if missing
            if report.get("created_timestamp") is None:
                report["created_timestamp"] = timezone.make_aware(timezone.datetime(1970, 1, 1))

            for week in matches_by_week:
                # Only look at reports, that currently exist
                if report.get("created_timestamp") < week["end_monday"]:
                    # If the report was created this week, count "new".
                    if report.get("created_timestamp") >= week["begin_monday"]:
                        week["new"] += 1
                    # If the report is not handled, or is handled in the future, count "matches".
                    if report.get("resolution_time") is None \
                            or report.get("resolution_time") > week["end_monday"]:
                        week["matches"] += 1
                    # If the report was handled in the past, don't count it.
                    elif report.get("resolution_time") < week["begin_monday"]:
                        continue
                    # If the report was handled this week, only count "handled".
                    elif report.get("resolution_time") < week["end_monday"]:
                        week["handled"] += 1

        return matches_by_week

    def managed_by(self, account):
        units = self.units.all() & account.get_managed_units()
        return units.exists()

    @property
    def is_manager(self):
        return self.get_managed_units().exists()

    @property
    def leadertab_access(self) -> bool:
        if (self.organization.leadertab_access == LeaderPageConfigChoices.MANAGERS
                and self.is_manager or self.user.is_superuser):
            return True
        elif (self.organization.leadertab_access == LeaderPageConfigChoices.SUPERUSERS
                and self.user.is_superuser):
            return True
        else:
            return False

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


class AccountBulkSerializer(BaseBulkSerializer):
    """ Bulk create & update logic lives in BaseBulkSerializer """
    class Meta:
        model = Account


class AccountSerializer(Core_AccountSerializer):

    pk = serializers.UUIDField(read_only=False)
    from ..models.organization import Organization
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=True,
        allow_null=False,
        pk_field=UUIDField(format='hex_verbose')
    )
    # Note that this is a PrimaryKeyRelatedField in the admin module.
    # Since manager is a self-referencing foreign-key however, we can't use that here, as we
    # cannot guarantee the manager Account exists in the database when doing bulk creates.
    manager = SelfRelatingField(
        queryset=Account.objects.all(),
        many=False,
        required=False,
        allow_null=True,
    )

    class Meta(Core_AccountSerializer.Meta):
        model = Account
        list_serializer_class = AccountBulkSerializer


Account.serializer_class = AccountSerializer


@receiver(post_delete, sender=Account)
def post_delete_user(sender, instance, *args, **kwargs):
    if instance.user:
        instance.user.delete()
