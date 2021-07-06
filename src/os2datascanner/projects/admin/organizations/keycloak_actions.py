from typing import Tuple, Sequence
from django.db import transaction

from os2datascanner.utils.ldap import RDN, LDAPNode
from os2datascanner.utils.system_utilities import time_now

from ..import_services.models.realm import Realm
from ..import_services import keycloak_services
from .models import (Alias, Account, Position,
        Organization, OrganizationalUnit)
from .models.aliases import AliasType


def keycloak_dn_selector(d):
    attributes = d.get("attributes", {})
    name = attributes.get("LDAP_ENTRY_DN", [None])[0]
    if name:
        yield name


def keycloak_group_dn_selector(d):
    attributes = d.get("attributes", {})
    name = attributes.get("LDAP_ENTRY_DN", [None])[0]
    groups = attributes.get("memberOf", [])
    if name and groups:
        dn = RDN.dn_to_sequence(name)
        for group_name in groups:
            gdn = RDN.dn_to_sequence(group_name)
            if gdn:  # Only yield names for valid groups
                yield RDN.sequence_to_dn(gdn + (dn[-1],))


def _dummy_pc(action, *args):
    pass


def perform_import(
        realm: Realm,
        progress_callback = _dummy_pc) -> Tuple[int, int, int]:
    """Collects the user hierarchy from the specified realm and creates
    local OrganizationalUnits and Accounts to reflect it. Local objects
    previously imported by this function but no longer backed by an object
    returned by Keycloak will be deleted.

    Returns a tuple of counts of objects that were added, updated, and
    removed."""
    now = time_now()
    org = realm.organization
    import_service = org.importservice
    if not import_service or not import_service.ldapconfig:
        return (0, 0, 0)

    name_selector = keycloak_dn_selector
    if import_service.ldapconfig.import_into == "group":
        name_selector = keycloak_group_dn_selector

    token_message = keycloak_services.request_access_token()
    token_message.raise_for_status()
    token = token_message.json()["access_token"]

    # Timeout set to 30 minutes
    sync_message = keycloak_services.sync_users(
            realm.realm_id, realm.organization.pk, token, timeout=1800)
    sync_message.raise_for_status()

    # Retrieve a count on the amount of users in given Keycloak realm
    keycloak_user_count = keycloak_services.get_user_count_in_realm(
        realm.realm_id, token, timeout=1800)

    # TODO: In the future this kind of logic should be reimplemented using websockets.
    # Gets all users in the given realm
    # Timeout set to 30 minutes
    user_message = keycloak_services.get_users(
        realm.realm_id, token, timeout=1800, max_users=keycloak_user_count)
    user_message.raise_for_status()
    remote = user_message.json()

    # XXX: is this correct? It seems to presuppose the existence of a top unit,
    # which the database doesn't actually specify or require
    local_top = OrganizationalUnit.objects.filter(imported=True,
            parent=None, organization=org).first()

    def account_to_node(
            a: Account, *, parent_path: Sequence[RDN] = ()) -> LDAPNode:
        full_path = RDN.dn_to_sequence(a.imported_id) if a.imported_id else ()
        local_path_part = RDN.drop_start(full_path, parent_path)
        return LDAPNode.make(
                local_path_part,
                id=a.uuid,
                firstName=a.first_name,
                lastName=a.last_name)

    def unit_to_node(
            ou: OrganizationalUnit, *,
            parent_path: Sequence[RDN] = ()) -> LDAPNode:
        full_path = (
                RDN.dn_to_sequence(ou.imported_id) if ou.imported_id else ())
        local_path_part = RDN.drop_start(full_path, parent_path)
        return LDAPNode.make(
                local_path_part,
                *(unit_to_node(c, parent_path=full_path)
                        for c in ou.children.all()),
                *(account_to_node(c, parent_path=full_path)
                        for c in ou.account_set.all()))

    # Convert the local objects to a LDAPNode so that we can use its diff
    # operation

    local_hierarchy = (
            unit_to_node(local_top)
            if local_top
            else LDAPNode.make(()))

    remote_hierarchy = LDAPNode.from_iterator(
            remote, name_selector=name_selector)
    # Collapse the top of the hierarchy together, but don't go further than the
    # first "ou" or "cn" -- groups and organisational units should be preserved
    remote_hierarchy = remote_hierarchy.collapse(
            lambda n: n.children[0].label[0].key not in ("ou", "cn"))

    to_add = []
    to_delete = Account.objects.none()
    to_update = Account.objects.none()

    units = {}
    accounts = {}

    def path_to_unit(
            o: Organization,
            path: Sequence[RDN]) -> OrganizationalUnit:
        unit_id = RDN.sequence_to_dn(path)
        unit = units.get(path)
        if unit == None:
            try:
                unit = OrganizationalUnit.objects.get(imported_id=unit_id)
            except OrganizationalUnit.DoesNotExist:
                label = path[-1].value if path else ""

                # We can't just call path_to_unit(o, path[:-1]) here, because
                # we have to make sure that our units actually match what the
                # hierarchy specifies without creating extra nodes
                parent = None
                if path:
                    path_fragment = path[:-1]
                    while path_fragment and not parent:
                        parent = units.get(path_fragment)
                        path_fragment = path_fragment[:-1]
        
                unit = OrganizationalUnit(
                        imported_id=RDN.sequence_to_dn(path),
                        name=label, parent=parent, organization=o,
                        # Clear the MPTT tree fields for now -- they get
                        # recomputed after we do bulk_create
                        lft=0, rght=0, tree_id=0, level=0)
                to_add.append(unit)
            units[path] = unit
        return unit

    def node_to_account(
            o: Organization,
            path: Sequence[RDN],
            node: LDAPNode) -> Account:
        uuid = node.properties["id"]
        account = accounts.get(uuid)
        if account == None:
            try:
                account = Account.objects.get(
                        organization=o, uuid=node.properties["id"])
            except Account.DoesNotExist:
                account = Account(
                    imported_id=RDN.sequence_to_dn(path),
                    uuid=node.properties["id"],
                    username=node.properties["username"],
                    first_name=node.properties["firstName"],
                    last_name=node.properties["lastName"],
                    organization=o)
                to_add.append(account)
            accounts[uuid] = account
        return account

    # Make sure that we have an OrganizationalUnit hierarchy that reflects the
    # remote one
    for path, r in remote_hierarchy.walk():
        if not path or not r.children:
            continue
        path_to_unit(org, path)

    diff = list(local_hierarchy.diff(remote_hierarchy))
    progress_callback("diff_computed", len(diff))

    # See what's changed
    for path, l, r in diff:
        # We're only interested in leaf nodes (accounts) here
        if not path or (l and l.children) or (r and r.children):
            progress_callback("diff_ignored", path)
            continue
        if l and not r:
            # A local object with no remote counterpart. Delete it
            to_delete |= Account.objects.filter(
                    imported_id=RDN.sequence_to_dn(path))
        else:
            # The remote object exists
            if not l:
                # ... and it has no local counterpart. Create one
                try:
                    account = node_to_account(org, path, r)
                except KeyError as ex:
                    # Missing required attribute -- skip this object
                    progress_callback("diff_ignored", path)
                    continue
                unit = path_to_unit(org, path[:-1])
                to_add.append(Position(account=account, unit=unit))
            else:
                # This should always work -- local_hierarchy has been built on
                # the basis of local database objects
                account = Account.objects.get(
                        imported_id=RDN.sequence_to_dn(path))

            mail_address = r.properties.get("email")
            if mail_address:
                try:
                    Alias.objects.get(
                            account=account,
                            _alias_type=AliasType.EMAIL.value,
                            value=mail_address)
                except Alias.DoesNotExist:
                    # The same user (mail_address) can be a member of multiple groups
                    # or org. units, so we need make sure we only create mail alias
                    # once.
                    alias_object = Alias(account=account,
                                         alias_type=AliasType.EMAIL,
                                         value=mail_address)
                    if alias_object not in to_add:
                        to_add.append(alias_object)
                except Alias.MultipleObjectsReturned:
                    # This state should not be possible, however if more than one
                    # Alias exists ignore.
                    pass

            # XXX: also update other stored properties

            progress_callback("diff_handled", path)

    with transaction.atomic():
        to_delete.delete()

        if to_add:
            for subset in (OrganizationalUnit, Account, Position, Alias,):
                manager = subset.objects

                instances = [o for o in to_add if isinstance(o, subset)]
                for o in instances:
                    o.imported = True
                    o.last_import = now
                    o.last_import_requested = now

                manager.bulk_create(instances)
                if hasattr(manager, "rebuild"):
                    manager.rebuild()

    return (len(to_add), len(to_update), len(to_delete))
