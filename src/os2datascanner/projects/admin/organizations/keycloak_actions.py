from typing import Tuple, Sequence
from django.db import transaction

from os2datascanner.utils.ldap import RDN, LDAPNode
from os2datascanner.utils.system_utilities import time_now

from ..import_services.models.realm import Realm
from ..import_services import keycloak_services
from .models import (Alias, Account, Position,
        Organization, OrganizationalUnit)
from .models.aliases import AliasType


@transaction.atomic
def perform_import(realm: Realm) -> Tuple[int, int, int]:
    """Collects the user hierarchy from the specified realm and creates
    local OrganizationalUnits and Accounts to reflect it. Local objects
    previously imported by this function but no longer backed by an object
    returned by Keycloak will be deleted.

    Returns a tuple of counts of objects that were added, updated, and
    removed."""
    now = time_now()
    org = realm.organization

    token_message = keycloak_services.request_access_token()
    token_message.raise_for_status()
    token = token_message.json()["access_token"]

    user_message = keycloak_services.get_users(realm.realm_id, token)
    user_message.raise_for_status()
    remote = user_message.json()

    # XXX: is this correct? It seems to presuppose the existence of a top unit,
    # which the database doesn't actually specify or require
    local_top = OrganizationalUnit.objects.filter(imported=True,
            parent=None, organization=org).first()

    def account_to_node(
            a: Account, *, parent_path: Sequence[RDN] = ()) -> LDAPNode:
        full_path = RDN.make_sequence(
                *a.imported_id.split(",")) if a.imported_id else ()
        local_path_part = RDN.drop_start(full_path, parent_path)
        return LDAPNode.make(
                local_path_part,
                id=a.uuid,
                firstName=a.first_name,
                lastName=a.last_name)

    def unit_to_node(
            ou: OrganizationalUnit, *,
            parent_path: Sequence[RDN] = ()) -> LDAPNode:
        full_path = RDN.make_sequence(
                *ou.imported_id.split(",")) if ou.imported_id else ()
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
            remote,
            dn_selector=lambda item: item["attributes"]["LDAP_ENTRY_DN"][0])
    # Collapse the top of the hierarchy together, but don't go further than the
    # first "ou" -- organisational units should be preserved
    remote_hierarchy = remote_hierarchy.collapse(
            lambda n: n.children[0].label[0].key != "ou")

    to_add = []
    to_delete = Account.objects.none()
    to_update = Account.objects.none()

    units = {}

    def path_to_unit(
            o: Organization,
            path: Sequence[RDN]) -> OrganizationalUnit:
        unit_id = RDN.make_string(path)
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
                        imported_id=RDN.make_string(path),
                        name=label, parent=parent, organization=o)
                to_add.append(unit)
            units[path] = unit
        return unit

    def node_to_account(
            o: Organization,
            path: Sequence[RDN],
            node: LDAPNode) -> Account:
        return Account(
                imported_id=RDN.make_string(path),
                uuid=node.properties["id"],
                username=node.properties["username"],
                first_name=node.properties["firstName"],
                last_name=node.properties["lastName"],
                organization=o)

    # Make sure that we have an OrganizationalUnit hierarchy that reflects the
    # remote one
    for path, r in remote_hierarchy.walk():
        if not path or not r.children:
            continue
        path_to_unit(org, path)

    # See what's changed
    for path, l, r in local_hierarchy.diff(remote_hierarchy):
        # We're only interested in leaf nodes (accounts) here
        if not path or (l and l.children) or (r and r.children):
            continue
        if l and not r:
            # A local object with no remote counterpart. Delete it
            to_delete |= Account.objects.filter(
                    imported_id=RDN.make_string(path))
        else:
            # The remote object exists
            if not l:
                # ... and it has no local counterpart. Create one
                try:
                    account = node_to_account(org, path, r)
                except KeyError as ex:
                    # Missing required attribute -- skip this object
                    continue
                unit = path_to_unit(org, path[:-1])
                to_add.append(account)
                to_add.append(Position(account=account, unit=unit))
            else:
                # This should always work -- local_hierarchy has been built on
                # the basis of local database objects
                account = Account.objects.get(
                        imported_id=RDN.make_string(path))

            mail_address = r.properties.get("email")
            if mail_address:
                try:
                    Alias.objects.get(
                            account=account,
                            _alias_type=AliasType.EMAIL.value,
                            value=mail_address)
                except Alias.DoesNotExist:
                    to_add.append(Alias(account=account,
                                        alias_type=AliasType.EMAIL,
                                        value=mail_address))

            # XXX: also update other stored properties
            pass

    # XXX: we should really use the bulk handling functions here, but they
    # seem not to preserve MPTT invariants(?)
    if to_add:
        for subset in (OrganizationalUnit, Account, Position, Alias,):
            for h in filter(lambda obj: isinstance(obj, subset), to_add):
                h.imported = True
                h.last_import_requested = now
                h.last_import = now
                h.save()

    if to_delete:
        for subset in (OrganizationalUnit, Account, Position,):
            for h in filter(lambda obj: isinstance(obj, subset), to_delete):
                h.delete()

    return (len(to_add), len(to_update), len(to_delete))
