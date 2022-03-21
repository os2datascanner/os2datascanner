import logging

# TODO: Should Aliases be created?
from .models import (Account, Position,
                     Organization, OrganizationalUnit)

logger = logging.getLogger(__name__)


# TODO: Handle .get() defaults so it doesn't break DB constraints on missing values
def perform_msgraph_import(data: list, organization: Organization):
    for group in data:
        org_unit_obj, created = OrganizationalUnit.objects.update_or_create(
            name=group.get("name"),
            organization=organization
        )
        print(f' Org Unit {org_unit_obj.name},'
              f' Created: {created}')

        for member in group['members']:
            if member.get('type') == 'user':
                member_obj, created = Account.objects.update_or_create(
                    username=member.get('userPrincipalName'),
                    first_name=member.get('givenName'),
                    last_name=member.get('surname'),
                    organization=organization
                )
                print(f' Member {member_obj.username},'
                      f' Created: {created}')

                position_obj, created = Position.objects.update_or_create(
                    account=member_obj,
                    unit=org_unit_obj,
                )
                print(f'Position for account {position_obj.account.username} '
                      f'in {position_obj.unit.name}, '
                      f'Created: {created}')
