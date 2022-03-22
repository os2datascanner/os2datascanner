import logging
import requests
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ...core.models.background_job import BackgroundJob
from os2datascanner.engine2.utilities.backoff import WebRetrier
from os2datascanner.engine2.model.msgraph.utilities import MSGraphSource

logger = logging.getLogger(__name__)

# Consider moving GraphCaller out of MSGraphSource.
GraphCaller = MSGraphSource.GraphCaller
# We don't need the MSGraphSource itself here, but GraphCaller is useful
# Deleting MSGraphSource from this module's globals.
del MSGraphSource


def _make_token_endpoint(tenant_id):
    return "https://login.microsoftonline.com/{0}/oauth2/v2.0/token".format(
        tenant_id)


class MSGraphImportJob(BackgroundJob):
    tenant_id = models.CharField(max_length=256, verbose_name="Tenant ID",
                                 null=False)

    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.PROTECT,
        verbose_name=_('organization'),
        related_name='msimport'
    )

    handled = models.IntegerField(null=True, blank=True)
    to_handle = models.IntegerField(null=True, blank=True)

    def make_token(self):
        response = WebRetrier().run(
            requests.post,
            _make_token_endpoint(self.tenant_id),
            {
                "client_id": settings.MSGRAPH_APP_ID,
                "scope": "https://graph.microsoft.com/.default",
                "client_secret": settings.MSGRAPH_CLIENT_SECRET,
                "grant_type": "client_credentials"
            })
        response.raise_for_status()
        logger.info("Collected new token")
        return response.json()["access_token"]

    @property
    def progress(self):
        return (self.handled / self.to_handle
                if self.handled is not None and self.to_handle not in (0, None)
                else None)

    @property
    def job_label(self) -> str:
        return "MSGraph Import Job"

    # TODO: Remember to set "status" & handle progress
    def run(self):
        data_type_user = "#microsoft.graph.user"
        data_type_group = "#microsoft.graph.group"
        hierarchy = list()
        group_info = dict()
        group_members = list()

        self.status = "Initializing MSGraph AAD Import..."
        self.save()

        with requests.Session() as session:
            gc = GraphCaller(self.make_token, session)
            groups = gc.paginated_get("groups")

            for group in groups:
                uuid = group["id"]  # We absolutely need an id.
                dn = group.get("displayName", "No display name")
                # Store group info in dict
                group_info['uuid'] = uuid
                group_info['name'] = dn

                # Check for transitive members of current group
                transitive_members = gc.paginated_get(f'groups/{uuid}/transitiveMembers')

                # TODO: Should we include groups with no members?
                if transitive_members:
                    for member in transitive_members:
                        if member['@odata.type'] == data_type_group:
                            group_members.append({
                                "type": "group",
                                "uuid": member.get("id"),
                                "displayName": member.get("displayName", "Unnamed group")

                            })

                        if member['@odata.type'] == data_type_user:
                            group_members.append({
                                "type": "user",
                                "uuid": member.get("id"),
                                "givenName": member.get("givenName", "No first name"),
                                "surname": member.get("surname", "No surname"),
                                "userPrincipalName": member.get("userPrincipalName", "No "
                                                                                     "principal "
                                                                                     "name")
                            })
                        else:
                            # Not an object of interest. Pass.
                            pass

                    # Copy objects and then clear. Otherwise, referenced objects will be lost
                    group_info["members"] = group_members.copy()
                    hierarchy.append(group_info.copy())
                    group_info.clear()
                    group_members.clear()

        from ...organizations.msgraph_import_actions import perform_msgraph_import

        def _callback(*args):
            # TODO: Implement a way to track progress
            pass

        self.status = "OK.. Data received, build and store relations..."
        self.save()
        perform_msgraph_import(hierarchy, self.organization)
