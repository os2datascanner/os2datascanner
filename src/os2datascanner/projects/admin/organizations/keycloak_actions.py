from typing import Tuple, Sequence
from django.db import transaction
import logging
from os2datascanner.utils.ldap import RDN, LDAPNode
from .utils import group_into, set_imported_fields, create_and_serialize, update_and_serialize, \
    delete_and_listify
from ..organizations.broadcast_bulk_events import (BulkCreateEvent, BulkUpdateEvent,
                                                   BulkDeleteEvent)
from ..adminapp.signals_utils import suppress_signals
from ..organizations.publish import publish_events
from ..import_services.models.realm import Realm
from ..import_services import keycloak_services
from .models import (Alias, Account, Position,
                     Organization, OrganizationalUnit)
from .models.aliases import AliasType


logger = logging.getLogger(__name__)
# TODO: Place somewhere reusable, or find a smarter way to ID aliases imported_id..
EMAIL_ALIAS_IMPORTED_ID_SUFFIX = "/email"


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
        progress_callback=_dummy_pc) -> Tuple[int, int, int]:
    """Collects the user hierarchy from the specified realm and creates
    local OrganizationalUnits and Accounts to reflect it. Local objects
    previously imported by this function but no longer backed by an object
    returned by Keycloak will be deleted.

    Returns a tuple of counts of objects that were added, updated, and
    removed."""
    org = realm.organization
    import_service = org.importservice
    if not import_service or not import_service.ldapconfig:
        return 0, 0, 0

    name_selector = keycloak_dn_selector
    if import_service.ldapconfig.import_into == "group":
        name_selector = keycloak_group_dn_selector

    token = keycloak_services.request_access_token()
    # Timeout set to 30 minutes
    sync_message = keycloak_services.sync_users(
            realm.realm_id, realm.organization.pk, token=token, timeout=1800)
    sync_message.raise_for_status()

    # TODO: In the future this kind of logic should be reimplemented using
    # websockets.
    # Gets all users in the given realm
    # Timeout set to 30 minutes
    all_users = list(
            keycloak_services.iter_users(
                    realm.realm_id, token=token, timeout=1800, page_size=1000))

    return perform_import_raw(org, all_users, name_selector, progress_callback)


def _account_to_node(a: Account) -> LDAPNode:
    """Constructs a LDAPNode from an Account object."""
    local_path_part = RDN.dn_to_sequence(a.imported_id)[-1:]
    return LDAPNode.make(
            local_path_part,
            attributes={"LDAP_ENTRY_DN": [a.imported_id]},
            id=str(a.uuid),
            firstName=a.first_name,
            lastName=a.last_name)


def _unit_to_node(
        ou: OrganizationalUnit, *,
        parent_path: Sequence[RDN] = ()) -> LDAPNode:
    """Constructs a LDAPNode hierarchy from an OrganizationalUnit object,
    including nodes for every sub-unit and account."""
    full_path = (
            RDN.dn_to_sequence(ou.imported_id) if ou.imported_id else ())
    local_path_part = RDN.drop_start(full_path, parent_path)
    return LDAPNode.make(
            local_path_part,
            *(_unit_to_node(c, parent_path=full_path)
              for c in ou.children.all()),
            *(_account_to_node(c) for c in ou.account_set.all()))


def _node_to_iid(path: Sequence[RDN], node: LDAPNode) -> str:
    """Generates the Imported.imported_id for an LDAPNode at a specified
    position in the hierarchy.

    For organisational units, this will just be the DN specified by the
    hierarchy, as OUs have no independent existence in OS2datascanner. For
    users, though, the canonical DN is used instead, as a user might appear at
    multiple positions (if they're a member of several groups, for example.)"""
    if node.children:  # The node is a group/OU
        return RDN.sequence_to_dn(path)
    else:  # The node is a user
        return node.properties["attributes"]["LDAP_ENTRY_DN"][0]


@suppress_signals.wrap
def perform_import_raw(  # noqa: C901, CCR001 too complex
        org: Organization,
        remote,
        name_selector,
        progress_callback=_dummy_pc):
    """The main body of the perform_import function, spun out into a separate
    function to allow for easier testing. Constructs a LDAPNode hierarchy from
    a Keycloak JSON response, compares it to an organisation's local hierarchy,
    and adds, updates and removes database objects to bring the local hierarchy
    into sync.

    Returns a tuple of counts of objects that were added, updated, and
    removed."""

    # XXX: is this correct? It seems to presuppose the existence of a top unit,
    # which the database doesn't actually specify or require
    local_top = OrganizationalUnit.objects.filter(
        imported=True, parent=None, organization=org).first()

    # Convert the local objects to a LDAPNode so that we can use its diff
    # operation

    local_hierarchy = (
            _unit_to_node(local_top)
            if local_top
            else LDAPNode.make(()))

    remote_hierarchy = LDAPNode.from_iterator(
            remote, name_selector=name_selector)

    to_add = []
    to_delete = []
    to_update = []

    units = {}
    accounts = {}
    account_positions = {}

    def path_to_unit(
            o: Organization,
            path: Sequence[RDN]) -> OrganizationalUnit:
        unit_id = RDN.sequence_to_dn(path)
        unit = units.get(path)
        if unit is None:
            try:
                unit = OrganizationalUnit.objects.get(
                        organization=o, imported_id=unit_id)
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
                        imported_id=unit_id,
                        name=label, parent=parent, organization=o,
                        # Clear the MPTT tree fields for now -- they get
                        # recomputed after we do bulk_create
                        lft=0, rght=0, tree_id=0, level=0)
                to_add.append(unit)
            units[path] = unit
        return unit

    def node_to_account(
            o: Organization,
            node: LDAPNode) -> Account:
        # One Account object can have multiple paths (if it's a member of
        # several groups, for example), so we need to use the true DN as our
        # imported_id here
        account_id = node.properties["attributes"]["LDAP_ENTRY_DN"][0]
        account = accounts.get(account_id)
        if account is None:
            try:
                account = Account.objects.get(
                        organization=o, imported_id=account_id)
            except Account.DoesNotExist:
                account = Account(organization=o, imported_id=account_id,
                                  uuid=node.properties["id"])
                to_add.append(account)
            accounts[account_id] = account
        return account

    logger.info("Building remote hierarchy")

    # Make sure that we have an OrganizationalUnit hierarchy that reflects the
    # remote one
    iids_to_preserve = set()
    for path, r in remote_hierarchy.walk():
        if not path:
            continue

        iids_to_preserve.add(_node_to_iid(path, r))
        if not r.children:
            continue
        path_to_unit(org, path)

    if not iids_to_preserve:
        logger.warning(
                "no remote users or organisational units available for"
                f" organisation {org.name}; are you sure your LDAP settings"
                " are correct?")
        return 0, 0, 0

    logger.info("Constructing raw diff")

    diff = list(local_hierarchy.diff(remote_hierarchy))
    progress_callback("diff_computed", len(diff))

    changed_accounts = {}

    logger.info("Building database operations")

    # See what's changed
    for path, l, r in diff:
        if not path:
            # Ignore the contentless root node
            progress_callback("diff_ignored", path)
            continue

        iid = _node_to_iid(path, r or l)

        # Keycloak's UserRepresentation type has no required fields(!); we
        # can't do anything useful if we don't have the very basics, though
        if r and not all(n in r.properties for n in ("id", "attributes", "username",)):
            progress_callback("diff_ignored", path)
            continue

        if l and not r:
            # A local object with no remote counterpart
            logger.debug(f"l: {l}, r: {r}, deleting")
            try:
                to_delete.append(Account.objects.get(imported_id=iid))
            except Account.DoesNotExist:
                to_delete.append(
                        OrganizationalUnit.objects.get(imported_id=iid))
        elif not (r or l).children:
            # A remote user exists...
            if not l:
                logger.debug(f"l: {l}, r: {r}, creating")
                # ... and it has no local counterpart. Create one
                try:
                    account = node_to_account(org, r)
                except KeyError:
                    # Missing required attribute -- skip this object
                    progress_callback("diff_ignored", path)
                    continue
            else:
                # ... and it has a local counterpart. Retrieve it
                logger.debug(f"l: {l}, r: {r}, updating (maybe)")
                try:
                    account = Account.objects.get(imported_id=iid)
                except Account.DoesNotExist:
                    # This can only happen if an Account has changed its
                    # imported ID without changing its position in the tree
                    # (i.e., a user's DN has changed, but their group
                    # membership has not). Retrieve the object by the old ID --
                    # we'll update it in a moment
                    account = Account.objects.get(
                            imported_id=_node_to_iid(path, l))

            if iid not in changed_accounts:
                changed_accounts[iid] = (r, account)

            unit = path_to_unit(org, path[:-1])

            if account not in account_positions:
                account_positions[account] = []

            try:
                Position.objects.get(account=account, unit=unit, imported=True)
            except Position.DoesNotExist:
                position = Position(
                    imported=True,
                    account=account,
                    unit=unit)
                to_add.append(position)

            account_positions[account].append(unit)
            progress_callback("diff_handled", path)

    for iid, (remote_node, account) in changed_accounts.items():
        mail_address = remote_node.properties.get("email")
        imported_id = f"{account.imported_id}{EMAIL_ALIAS_IMPORTED_ID_SUFFIX}"
        # The user has an email. Create or update if necessary
        if mail_address:
            try:
                alias = Alias.objects.get(
                    imported_id=imported_id,
                    account=account,
                    _alias_type=AliasType.EMAIL)
                for attr_name, expected in (("_value", mail_address),):
                    if getattr(alias, attr_name) != expected:
                        setattr(alias, attr_name, expected)
                        to_update.append((alias, (attr_name,)))
            except Alias.DoesNotExist:
                alias = Alias(
                    imported_id=imported_id,
                    account=account,
                    _alias_type=AliasType.EMAIL,
                    _value=mail_address
                )
                if alias not in to_add:
                    to_add.append(alias)
        elif not mail_address:
            # The user no longer has an email - delete previously imported ones
            to_delete.extend(Alias.objects.filter(account=account,
                                                  imported=True,
                                                  _alias_type=AliasType.EMAIL))

        # Update the other properties of the account
        for attr_name, expected in (
                ("imported_id", iid),
                ("username", remote_node.properties["username"]),
                # Our database schema requires the name properties, so use the
                # empty string as the dummy value instead of None
                ("first_name", remote_node.properties.get("firstName", "")),
                ("last_name", remote_node.properties.get("lastName", ""))):
            if getattr(account, attr_name) != expected:
                setattr(account, attr_name, expected)
                to_update.append((account, (attr_name,)))

    # Make sure we don't try to delete objects that are still referenced in the
    # remote hierarchy
    to_delete = [t for t in to_delete if t.imported_id not in iids_to_preserve]
    # Figure out which positions to delete for each user.
    for acc in account_positions:
        positions_to_delete = Position.objects.filter(
            account=acc, imported=True).exclude(
            unit__in=account_positions[acc])
        if positions_to_delete:
            to_delete.extend(positions_to_delete)

    logger.info("Applying database operations")

    with transaction.atomic():
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Summarising LDAP transaction:")
            for manager, instances in group_into(
                    to_delete, Alias, Position, Account, OrganizationalUnit):
                logger.debug(f"{manager.model.__name__}:"
                             f" delete [{', '.join(str(i) for i in instances)}]")
            for manager, instances in group_into(
                    to_update, Alias, Position, Account, OrganizationalUnit,
                    key=lambda k: k[0]):
                properties = set()
                for _, props in instances:
                    properties |= set(props)
                instances = set(str(i) for i, _ in instances)
                logger.debug(f"{manager.model.__name__}:"
                             f" update fields ({', '.join(properties)})"
                             f" of [{', '.join(instances)}]")
            for manager, instances in group_into(
                    to_add, OrganizationalUnit, Account, Position, Alias):
                logger.debug(f"{manager.model.__name__}:"
                             f" add [{', '.join(str(i) for i in instances)}]")

        # Deletes
        delete_dict = {}
        for manager, instances in group_into(
                to_delete, Alias, Position, Account, OrganizationalUnit):

            model_name = manager.model.__name__
            delete_dict[model_name] = delete_and_listify(manager, instances)

        # Updates
        # TODO: We're not actually updating "Imported" fields/timestamps. Should we?
        update_dict = {}
        for manager, instances in group_into(
                to_update, Alias, Position, Account, OrganizationalUnit,
                key=lambda k: k[0]):

            model_name = manager.model.__name__
            update_dict[model_name] = update_and_serialize(manager, instances)

        # Creates
        # TODO: Place the order of which objects should be created/updated somewhere reusabled
        set_imported_fields(to_add)  # Updates imported_time etc.
        creation_dict = {}
        for manager, instances in group_into(
                to_add, OrganizationalUnit, Account, Position, Alias):

            model_name = manager.model.__name__
            creation_dict[model_name] = create_and_serialize(manager, instances)

        event = [BulkDeleteEvent(delete_dict), BulkCreateEvent(creation_dict),
                 BulkUpdateEvent(update_dict), ]
        logger.info("Database operations complete")
        publish_events(event)

    return len(to_add), len(to_update), len(to_delete)
