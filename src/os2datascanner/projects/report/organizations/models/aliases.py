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
from rest_framework import serializers
from rest_framework.fields import UUIDField
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from functools import reduce

from os2datascanner.core_organizational_structure.models import Alias as Core_Alias
from os2datascanner.core_organizational_structure.models import \
    AliasSerializer as Core_AliasSerializer
from os2datascanner.core_organizational_structure.models.aliases import AliasType, \
    validate_regex_SID  # noqa
from ..seralizer import BaseBulkSerializer


class AliasQuerySet(models.query.QuerySet):
    def associated_report_keys(self):
        return reduce(
                models.query.QuerySet.union,
                (alias.match_relation.all().values_list("pk", flat=True)
                 for alias in self),
                self.model.objects.none())

    def delete(self):
        # Avoid circular import
        from os2datascanner.projects.report.reportapp.management.commands.result_collector import \
            create_aliases
        from os2datascanner.projects.report.reportapp.models.documentreport import DocumentReport

        associated_report_keys = set(self.associated_report_keys())

        with transaction.atomic():
            rv = super().delete()
            for dr in DocumentReport.objects.filter(
                    pk__in=associated_report_keys,
                    raw_metadata__isnull=False):
                create_aliases(dr)
            return rv


class AliasManager(models.Manager):
    def get_queryset(self):
        return AliasQuerySet(self.model, using=self._db, hints=self._hints)


class Alias(Core_Alias):
    """ Core logic lives in the core_organizational_structure app. """
    objects = AliasManager()
    serializer_class = None
    user = models.ForeignKey(User, null=False, verbose_name=_('user'),
                             on_delete=models.CASCADE, related_name="aliases")

    # TODO: In the future, we want to use "account" instead of django's User objects.
    # However, for now, we don't - hence this field is nullable.
    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name='aliases',
        verbose_name=_('account'),
        blank=True,
        null=True
    )

    def delete(self, *args, **kwargs):
        # Defer to the QuerySet -- it cleans up in an optimised way
        return self._meta.model.objects.filter(pk=self.pk).delete()

    @property
    def key(self):
        return self.value

    def __str__(self):
        format_string = ('Alias ({type}) {value}')
        return format_string.format(
            type=self.alias_type.label,
            value=self.value,
        )


class AliasBulkSerializer(BaseBulkSerializer):
    class Meta:
        model = Alias

    @transaction.atomic
    def create(self, validated_data):
        aliases = [Alias(**alias_attrs) for alias_attrs in validated_data]
        for alias in aliases:
            # TODO: Fishy; correct when User/Acc merged.
            user_obj = User.objects.get(username=alias.account.username)
            alias.user = user_obj

        return Alias.objects.bulk_create(aliases)


class AliasSerializer(Core_AliasSerializer):
    pk = serializers.UUIDField(read_only=False)
    from ..models.account import Account
    account = serializers.PrimaryKeyRelatedField(
        queryset=Account.objects.all(),
        required=True,
        allow_null=False,
        # This will properly serialize uuid.UUID to str:
        pk_field=UUIDField(format='hex_verbose'))

    class Meta(Core_AliasSerializer.Meta):
        model = Alias
        list_serializer_class = AliasBulkSerializer


Alias.serializer_class = AliasSerializer
