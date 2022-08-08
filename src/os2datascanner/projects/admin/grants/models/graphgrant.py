from uuid import uuid4
from django.db import models

from os2datascanner.engine2.model.msgraph.utilities import make_token
from os2datascanner.projects.admin import settings
from .grant import Grant


class GraphGrant(Grant):
    """A GraphGrant represents an entitlement to use the Microsoft Graph API
    to explore the resources associated with a particular tenant.

    (Note that the specific permissions associated with this entitlement are
    not specified here, but in the OS2datascanner application registration in
    Microsoft's portal.)"""
    tenant_id = models.UUIDField(
            default=uuid4, editable=False, verbose_name="tenant ID")

    def make_token(self):
        return make_token(
                settings.MSGRAPH_APP_ID,
                str(self.tenant_id),
                settings.MSGRAPH_CLIENT_SECRET)

    def validate(self):
        return self.make_token() is not None

    def __str__(self):
        return f"Microsoft Graph access to tenant {self.tenant_id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                    fields=["organization", "tenant_id"],
                    name="avoid_multiple_overlapping_grants")
        ]
