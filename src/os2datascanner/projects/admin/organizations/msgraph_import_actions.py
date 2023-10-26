import logging
from .keycloak_actions import _dummy_pc
from .models import (Account, Alias, Position,
                     Organization, OrganizationalUnit)
from .models.aliases import AliasType
from .utils import prepare_and_publish
from ..adminapp.signals_utils import suppress_signals
from os2datascanner.utils.system_utilities import time_now

logger = logging.getLogger(__name__)

# TODO: Place somewhere reusable, or find a smarter way to ID aliases imported_id..
EMAIL_ALIAS_IMPORTED_ID_SUFFIX = "/email"
SID_ALIAS_IMPORTED_ID_SUFFIX = "/sid"


@suppress_signals.wrap
def perform_msgraph_import(data: list,  # noqa: C901, CCR001
                           organization: Organization,
                           progress_callback=_dummy_pc):
    account_positions = {}
    accounts = {}
    aliases = {}

    now = time_now()
    to_add = []
    to_update = []
    to_delete = []

    # Set to contain retrieved uuids - things we have locally but aren't present remotely
    # will be deleted.
    all_uuids = set()
    progress_callback("group_count", len(data))

    def evaluate_org_unit(group_element: dict) -> OrganizationalUnit:
        """ Evaluates given dictionary (which should be of one group/ou), decides if corresponding
        local object (if any) is to be updated, a new one is to be created or no actions.
        Returns an OrganizationalUnit object."""
        unit_imported_id = group_element.get("uuid")
        unit_name = group_element.get("name")

        try:
            org_unit = OrganizationalUnit.objects.get(
                organization=organization, imported_id=unit_imported_id)
            for attr_name, expected in (
                    ("name", unit_name),
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

        all_uuids.add(unit_imported_id)
        return org_unit

    def evaluate_group_member(member: dict) -> (Account, dict):  # noqa: CCR001
        """ Evaluates given dictionary (which should be of one member/account).
        Decides if corresponding local object (if any) is to be updated,
        a new one is to be created or no actions.
        Returns an Account object."""

        # Cases of no UPN have been observed and will cause database integrity error.
        # We use it as username -- and to have an account, that is the bare minimum.
        # Hence, if missing, we should not try to create the account.
        if member.get("userPrincipalName") and member.get('type') == 'user':
            imported_id = member.get("uuid")
            username = member.get("userPrincipalName")
            first_name = member.get("givenName", "")
            last_name = member.get("surname", "")
            manager_info = member.get("manager")

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
                account_positions[account] = []

            all_uuids.add(imported_id)
            return account, manager_info

        else:
            logger.info(f'Object not of type user or empty UPN for user: {member}')
            return None, None

    def evaluate_aliases(account: Account, email: str, sid: str):  # noqa: CCR001
        def get_or_update_alias(imported_id_suffix, alias_type, value):
            imported_id = f"{account.imported_id}{imported_id_suffix}"
            alias = aliases.get(imported_id)
            if alias is None:
                try:
                    alias = Alias.objects.get(
                        imported_id=imported_id,
                        account=account,
                        _alias_type=alias_type)
                    for attr_name, expected in (("_value", value),):
                        if getattr(alias, attr_name) != expected:
                            setattr(alias, attr_name, expected)
                            to_update.append((alias, (attr_name,)))

                except Alias.DoesNotExist:
                    alias = Alias(
                        imported_id=imported_id,
                        account=account,
                        _alias_type=alias_type,
                        _value=value
                    )
                    to_add.append(alias)
                aliases[imported_id] = alias
                all_uuids.add(imported_id)

        if email:
            get_or_update_alias(EMAIL_ALIAS_IMPORTED_ID_SUFFIX, AliasType.EMAIL.value, email)
        else:
            logger.info(f"No email for account {account.username}")

        if sid:
            get_or_update_alias(SID_ALIAS_IMPORTED_ID_SUFFIX, AliasType.SID.value, sid)
        else:
            logger.info(f"No SID for account {account.username}")

    manager_relations = {}
    for group in data:
        unit = evaluate_org_unit(group)
        for member in group['members']:
            acc, manager_info = evaluate_group_member(member)
            manager_id = manager_info.get("id") if manager_info else None
            if manager_id:
                manager_relations[acc] = manager_id
            if acc:
                evaluate_aliases(account=acc,
                                 email=member.get("email"),
                                 sid=member.get("sid"))

                try:
                    Position.objects.get(account=acc, unit=unit, imported=True)
                except Position.DoesNotExist:
                    position = Position(
                        imported=True,
                        account=acc,
                        unit=unit)
                    to_add.append(position)

                account_positions[acc].append(unit)

        progress_callback("group_handled", unit.name)

    # Sort out Account-manager relations
    for acc, manager_id in manager_relations.items():
        acc.manager = accounts.get(manager_id)

    # Figure out which positions to delete for each user.
    for acc in account_positions:
        positions_to_delete = Position.objects.filter(
            account=acc, imported=True).exclude(
            unit__in=account_positions[acc])
        if positions_to_delete:
            to_delete.append(positions_to_delete)

    prepare_and_publish(organization, all_uuids, to_add, to_delete, to_update)
