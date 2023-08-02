import logging
from .keycloak_actions import _dummy_pc

from .models import (Account, Alias, Position,
                     Organization, OrganizationalUnit)
from .models.aliases import AliasType
from os2datascanner.utils.system_utilities import time_now
from .utils import prepare_and_publish
from ..adminapp.signals_utils import suppress_signals

logger = logging.getLogger(__name__)

# TODO: Place somewhere reusable, or find a smarter way to ID aliases imported_id..
EMAIL_ALIAS_IMPORTED_ID_SUFFIX = "/email"


@suppress_signals.wrap
def perform_os2mo_import(org_unit_list: list,  # noqa: CCR001, C901 too high cognitive complexity
                         organization: Organization,
                         progress_callback=_dummy_pc):
    accounts = {}
    aliases = {}
    account_employee_positions = {}
    account_manager_positions = {}
    ous = {}
    ou_parent_relations = {}

    now = time_now()

    to_add = []
    position_hashes = set()

    to_update = []
    to_delete = []

    # Set to contain retrieved uuids - things we have locally but aren't present remotely
    # will be deleted.
    all_uuids = set()
    progress_callback("org_unit_count", len(org_unit_list))

    def evaluate_org_unit(unit_raw: dict) -> (OrganizationalUnit, dict):
        """ Evaluates given dictionary (which should be of one ou), decides if corresponding
        local object (if any) is to be updated, a new one is to be created or no actions.
        Returns an OrganizationalUnit object."""
        unit_imported_id = unit_raw.get("uuid")
        unit_name = unit_raw.get("name")
        unit_parent_info = unit_raw.get("parent")
        unit_parent_id = unit_parent_info.get("uuid", None) if unit_parent_info else None

        try:
            org_unit = OrganizationalUnit.objects.get(
                organization=organization, imported_id=unit_imported_id)
            for attr_name, expected in (
                    ("name", unit_name),
                    ("parent_id", unit_parent_id)
            ):
                if getattr(org_unit, attr_name) != expected:
                    setattr(org_unit, attr_name, expected)
                    to_update.append((org_unit, (attr_name,)))

        except OrganizationalUnit.DoesNotExist:
            org_unit = OrganizationalUnit(
                imported_id=unit_imported_id,
                organization=organization,
                name=unit_name,
                imported=True,
                last_import=now,
                last_import_requested=now,
                lft=0, rght=0, tree_id=0, level=0
            )
            to_add.append(org_unit)

        ous[unit_imported_id] = org_unit
        all_uuids.add(unit_imported_id)
        return org_unit, unit_parent_info

    def evaluate_unit_member(member: dict, role: str) -> Account or None:
        imported_id = member.get("uuid")
        username = member.get("user_key", None)
        first_name = member.get("givenname", "")
        last_name = member.get("surname", "")

        if not username:
            logger.info(f'Object not a user or empty user key for user: {member}')
            return None

        account = accounts.get(imported_id)
        if account is None:
            try:
                account = Account.objects.get(
                    organization=organization, imported_id=imported_id)
                for attr_name, expected in (
                        ("username", username),
                        ("first_name", first_name),
                        ("last_name", last_name),
                ):
                    if getattr(account, attr_name) != expected:
                        setattr(account, attr_name, expected)
                        to_update.append((account, (attr_name,)))

            except Account.DoesNotExist:
                account = Account(
                    imported_id=imported_id,
                    organization=organization,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                to_add.append(account)
                accounts[imported_id] = account

            all_uuids.add(imported_id)

        # TODO: Don't evaluate on raw strings
        if role == "employee":
            account_employee_positions[account] = []
        if role == "manager":
            account_manager_positions[account] = []
        return account

    def evaluate_aliases(account: Account, email: str):
        imported_id = f"{account.imported_id}{EMAIL_ALIAS_IMPORTED_ID_SUFFIX}"
        alias = aliases.get(imported_id)
        if alias is None:
            try:
                alias = Alias.objects.get(
                    imported_id=imported_id,
                    account=account,
                    _alias_type=AliasType.EMAIL.value)
                for attr_name, expected in (("_value", email),):
                    if getattr(alias, attr_name) != expected:
                        setattr(alias, attr_name, expected)
                        to_update.append((alias, (attr_name,)))

            except Alias.DoesNotExist:
                alias = Alias(
                    imported_id=imported_id,
                    account=account,
                    _alias_type=AliasType.EMAIL.value,
                    _value=email
                )
                to_add.append(alias)
            aliases[imported_id] = alias
            all_uuids.add(imported_id)

    def get_email_address(employee_elm: list) -> str:
        try:
            empl_email = employee_elm[0].get("addresses")[0].get(
                "name")
        except BaseException:
            empl_email = None
            logger.info(f'No email in: {employee_elm[0]}')
        return empl_email

    def positions_to_add(acc: Account, unit: OrganizationalUnit, role: str):
        """ Helper function that appends positions to to_add if not present locally """
        try:
            Position.objects.get(account=acc, unit=unit, role=role, imported=True)
        except Position.DoesNotExist:
            position = Position(
                imported=True,
                account=acc,
                unit=unit,
                role=role,)
            position_hash = hash(str(acc.uuid) + str(unit.uuid) + role)

            # There's a chance we've already added this position to the list,
            # due to how the data we receive looks.
            if position_hash not in position_hashes:
                to_add.append(position)
                position_hashes.add(position_hash)

        # TODO: Comment above also means we're potentially appending the same unit n times,
        # which has no functionality breaking consequences, but is waste of space.
        if role == "employee":
            account_employee_positions[acc].append(unit)
        if role == "manager":
            account_manager_positions[acc].append(unit)

    def positions_to_delete():
        """Helper function that figures out which position objects are to be deleted.
        Adds positions to to_delete list.
        Returns nothing."""
        for empl_acc in account_employee_positions:
            employee_positions_to_delete = Position.objects.filter(
                account=empl_acc, imported=True, role="employee").exclude(
                unit__in=account_employee_positions[empl_acc])
            if positions_to_delete:
                to_delete.append(employee_positions_to_delete)
            else:
                continue
        for man_acc in account_manager_positions:
            manager_positions_to_delete = Position.objects.filter(
                account=man_acc, imported=True, role="manager").exclude(
                unit__in=account_manager_positions[man_acc])
            if positions_to_delete:
                to_delete.append(manager_positions_to_delete)
            else:
                continue

    for data in org_unit_list:
        for org_unit_raw in data.get("objects"):
            # Evaluate org units and store their parent-relations.
            unit, parent_info = evaluate_org_unit(org_unit_raw)
            parent_id = parent_info.get("uuid") if parent_info else None
            if parent_id:
                ou_parent_relations[unit] = parent_id

            for employees in org_unit_raw.get("engagements"):
                employee = employees.get("employee", None)
                if not employee:
                    logger.info(f'Encountered an empty employee dict in: {unit} \n'
                                f'Continuing..')
                    continue
                # Index zero - an employee comes in list form
                acc = evaluate_unit_member(member=employee[0], role="employee")
                if acc:
                    # TODO: This feels fragile.. and potentially soon needs support for SID
                    # Look to refactor from MSGraph import actions and generalize logic.
                    employee_email = get_email_address(employee)
                    if employee_email:
                        evaluate_aliases(account=acc, email=employee_email)

                    positions_to_add(acc=acc, unit=unit, role="employee")

            for managers in org_unit_raw.get("managers"):
                manager = managers.get("employee", None)
                if not manager:
                    logger.info(f'Encountered an empty employee dict in: {unit} \n'
                                f'Continuing..')
                    continue
                acc = evaluate_unit_member(member=manager[0], role="manager")

                if acc:
                    # TODO: This feels fragile.. and potentially soon needs support for SID
                    # Look to refactor from MSGraph import actions and generalize logic.
                    manager_email = get_email_address(manager)
                    if manager_email:
                        evaluate_aliases(account=acc, email=manager_email)

                    positions_to_add(acc=acc, unit=unit, role="manager")

    # Sort out OU-parent relations
    for ou, parent_id in ou_parent_relations.items():
        ou.parent = ous.get(parent_id)

    # Append positions to to_delete
    positions_to_delete()
    # ... then, execute
    prepare_and_publish(all_uuids, to_add, to_delete, to_update)
