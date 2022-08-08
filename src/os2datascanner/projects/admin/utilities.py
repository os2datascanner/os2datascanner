"""
"""

from typing import Optional

from django.contrib.auth.models import User
from django.db.models.query_utils import Q

from os2datascanner.projects.admin.core.models import Client
from os2datascanner.projects.admin.organizations.models import Organization


class UserWrapper:
    def __init__(self, user: User):
        self.user = user

    def __str__(self):
        return f"[[{str(self.user)}]]"

    def __repr__(self):
        return f"[[{repr(self.user)}]]"

    def make_org_Q(self, org_path: str = "organization") -> Q:
        """Returns a Q object that selects all objects whose Organization the
        wrapped User can interact with. (Note that this might, in the worst
        case, mean *no* objects.)"""
        if self.user.is_superuser:
            return Q()
        elif (client := self.get_client()):
            uuids = {org.uuid for org in client.organizations.all()}
            return Q(**{org_path + "__in": uuids})
        else:
            return Q(pk__isnull=True)

    def get_client(self) -> Optional[Client]:
        """Returns the Client object for which the wrapped User is an
        administrator, or None if there isn't one."""
        client = None
        if hasattr(self.user, 'administrator_for'):
            client = self.user.administrator_for.client
        return client

    def get_org(self) -> Organization:
        """Attempts to relate the wrapped User to precisely one Organization,
        and returns that Organization. (Note that this will raise either the
        DoesNotExist or MultipleObjectsReturned exception if it fails.)"""
        return Organization.objects.filter(self.make_org_Q("uuid")).get()
