import logging
from django.db import transaction

from .models import (Account, Alias, Position,
                     Organization, OrganizationalUnit)
from .models.aliases import AliasType
from os2datascanner.utils.system_utilities import time_now

logger = logging.getLogger(__name__)


# TODO: Try to bring down complexity.
@transaction.atomic
def perform_msgraph_import(data: list,  # noqa: CCR001, too high cognitive complexity
                           organization: Organization):
    now = time_now()
    # Set to contain retrieved uuids - things we have locally but aren't present remotely
    # will be deleted.
    all_uuids = set()

    # Position & Alias objects are initially told to be deleted, to ensure we have a correct
    # reflection of remote.
    Position.objects.filter(imported=True).delete()
    Alias.objects.filter(imported=True).delete()

    for group in data:
        org_unit_obj, created = OrganizationalUnit.objects.update_or_create(
            imported_id=group.get("uuid"),
            imported=True,
            organization=organization,
            defaults={
                "last_import": now,
                "last_import_requested": now,
                "name": group.get("name")
            }
        )
        logger.info(f' Org Unit {org_unit_obj.name}, '
                    f'Created: {created if created else "Up-to-date"}')

        all_uuids.add(group.get("uuid"))

        for member in group['members']:
            if member.get('type') == 'user':
                account_obj, created = Account.objects.update_or_create(
                    imported_id=member.get("uuid"),
                    imported=True,
                    organization=organization,
                    defaults={
                        "last_import": now,
                        "last_import_requested": now,
                        "username": member.get("userPrincipalName"),
                        "first_name": member.get("givenName"),
                        "last_name": member.get("surname")
                    }
                )
                logger.info(f' Member {account_obj.username}, '
                            f'Created: {created if created else "Up-to-date"}')

                if not member.get("email"):
                    logger.info(f'No Email for account {account_obj.username}')
                else:
                    # Position and alias objects are deleted every time we import
                    # which means that doing update or create will always be a "create", so it
                    # might be unnecessary to use update_or_create
                    alias_obj, created = Alias.objects.update_or_create(
                        imported_id=member.get("uuid"),  # Note: Same ID as for the account obj.
                        imported=True,
                        account=account_obj,
                        _alias_type=AliasType.EMAIL.value,
                        defaults={
                            "last_import": now,
                            "last_import_requested": now,
                            "value": member.get("email")
                        }
                    )
                    logger.info(f'Alias for account {alias_obj.account.username} '
                                f'Created: {created if created else "Up-to-date"}')

                # This comes from an on prem AD
                if not member.get("sid"):
                    logger.info(f'No SID for account {account_obj.username}')
                else:
                    sid_alias_obj, created = Alias.objects.update_or_create(
                        imported_id=member.get("uuid"),  # Note: Same ID as for the account obj.
                        imported=True,
                        account=account_obj,
                        _alias_type=AliasType.SID.value,
                        defaults={
                            "last_import": now,
                            "last_import_requested": now,
                            "value": member.get('sid')
                        }
                    )
                    logger.info(f'SID Alias for account {sid_alias_obj.account.username} '
                                f'Created: {created if created else "Up-to-date"}')

                position_obj, created = Position.objects.update_or_create(
                    imported=True,
                    account=account_obj,
                    unit=org_unit_obj,
                    defaults={
                        "last_import": now,
                        "last_import_requested": now
                    }
                )
                logger.info(f'Position for account {position_obj.account.username} '
                            f'in {position_obj.unit.name}, '
                            f'Created: {created if created else "Up-to-date"}')

                all_uuids.add(member.get("uuid"))

    # Deleting local objects no longer present remotely.
    Account.objects.exclude(imported_id__in=all_uuids).exclude(imported=False).delete()
    OrganizationalUnit.objects.exclude(imported_id__in=all_uuids).exclude(imported=False).delete()
