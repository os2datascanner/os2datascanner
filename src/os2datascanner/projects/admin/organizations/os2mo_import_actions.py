import logging
import string
from django.db import transaction
from .keycloak_actions import _dummy_pc

from .models import (Account, Alias, Position,
                     Organization, OrganizationalUnit)
from .models.aliases import AliasType
from os2datascanner.utils.system_utilities import time_now

logger = logging.getLogger(__name__)


# TODO: Try to bring down complexity.
@transaction.atomic
def perform_os2mo_import(data: list,  # noqa: CCR001, too high cognitive complexity
                         organization: Organization,
                         progress_callback=_dummy_pc):

    now = time_now()

    # Set to contain retrieved uuids - things we have locally but aren't present remotely
    # will be deleted.
    all_uuids = set()

    # Position & Alias objects are initially told to be deleted, to ensure we have a correct
    # reflection of remote.
    Position.objects.filter(imported=True).delete()
    Alias.objects.filter(imported=True).delete()

    progress_callback("org_unit_count", len(data))

    def add_unit(employees: dict, org_unit_obj: OrganizationalUnit, role: string):
        account_obj, created = Account.objects.update_or_create(
            imported_id=employees.get("employee")[0].get("uuid"),
            imported=True,
            organization=organization,
            defaults={
                "last_import": now,
                "last_import_requested": now,
                "username": employees.get("employee")[0].get("user_key"),
                "first_name": employees.get("employee")[0].get("givenname"),
                "last_name": employees.get("employee")[0].get("surname")
            }
        )
        logger.info(f'  Account {account_obj.username}, '
                    f'Created: {created if created else "Up-to-date"}')

        if not employees.get("employee")[0].get("addresses")[0].get("name"):
            logger.info(f'No Email for account {account_obj.username}')
        else:
            # Position and alias objects are deleted every time we import
            # which means that doing update or create will always be a "create", so it
            # might be unnecessary to use update_or_create
            alias_obj, created = Alias.objects.update_or_create(
                # Note: Same ID as for the account obj.
                imported_id=employees.get("employee")[0].get("uuid"),
                imported=True,
                account=account_obj,
                _alias_type=AliasType.EMAIL.value,
                defaults={
                    "last_import": now,
                    "last_import_requested": now,
                    "value": employees.get("employee")[0].get("addresses")[0].get("name")
                }
            )
            logger.info(f'    Alias for account {alias_obj.account.username} '
                        f'Created: {created if created else "Up-to-date"}')

            position_obj, created = Position.objects.update_or_create(
                imported=True,
                account=account_obj,
                unit=org_unit_obj,
                role=role,
                defaults={
                    "last_import": now,
                    "last_import_requested": now
                }
            )
            logger.info(
                f'    Position for {role.capitalize()} account {position_obj.account.username} '
                f'in {position_obj.unit.name}, '
                f'Created: {created if created else "Up-to-date"}')

        all_uuids.add(employees.get("employee")[0].get("uuid"))

    for object in data.get("data").get("org_units"):
        for org_unit in object.get("objects"):
            if org_unit.get("parent") is not None:
                parent, created = OrganizationalUnit.objects.update_or_create(
                    imported_id=org_unit.get("parent").get("uuid"),
                    imported=True,
                    organization=organization,
                    defaults={
                        "last_import": now,
                        "last_import_requested": now,
                        "name": org_unit.get("parent").get("name")
                    }
                )
                logger.info(
                    f'Parent {parent.name}, '
                    f'for {org_unit.get("name")}, Created: {created if created else "Up-to-date"}')
                org_unit_obj, created = OrganizationalUnit.objects.update_or_create(
                    imported_id=org_unit.get("uuid"),
                    imported=True,
                    organization=organization,
                    defaults={
                        "parent": parent,
                        "last_import": now,
                        "last_import_requested": now,
                        "name": org_unit.get("name")
                    }
                )
            else:
                org_unit_obj, created = OrganizationalUnit.objects.update_or_create(
                    imported_id=org_unit.get("uuid"),
                    imported=True,
                    organization=organization,
                    defaults={
                        "last_import": now,
                        "last_import_requested": now,
                        "name": org_unit.get("name")
                    }
                )
            logger.info(f'Org Unit {org_unit_obj.name}, '
                        f'Created: {created if created else "Up-to-date"}')

            progress_callback("org_unit_handled", org_unit_obj.name)

            all_uuids.add(org_unit.get("uuid"))

            for managers in org_unit.get("managers"):
                add_unit(managers, org_unit_obj, "manager")

            for employees in org_unit.get("associations"):
                add_unit(employees, org_unit_obj, "employee")

    # Deleting local objects no longer present remotely.
    Account.objects.exclude(imported_id__in=all_uuids).exclude(imported=False).delete()
    OrganizationalUnit.objects.exclude(imported_id__in=all_uuids).exclude(imported=False).delete()
