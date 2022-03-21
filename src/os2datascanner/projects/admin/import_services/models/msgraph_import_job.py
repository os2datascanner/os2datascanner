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


# TODO: Convert prints to logging & write more useful log messages

class MSGraphImportJob(BackgroundJob):
    tenant_id = models.CharField(max_length=256, verbose_name="Tenant ID",
                                 null=False)

    # Should maybe not be limited to "One"?
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
    # TODO: Try to bring down complexity and not just ignore it
    def run(self):  # noqa: CCR001, too high cognitive complexity
        data_type_user = "#microsoft.graph.user"
        data_type_group = "#microsoft.graph.group"
        # TODO: Perhaps do this in a smarter way
        hierarchy = list()
        group_info = dict()
        group_members = list()
        member_info = dict()
        group_child_info = dict()

        with requests.Session() as session:
            gc = GraphCaller(self.make_token, session)
            groups = gc.get("groups")

            # TODO: Consider using .get() instead of direct key lookups for better error handling
            for group in groups["value"]:
                uuid = group["id"]
                dn = group["displayName"]

                # Store group info in dict
                group_info['uuid'] = uuid
                group_info['name'] = dn

                # Check for transitive members of current group
                transitive_members = gc.get(f'groups/{uuid}/transitiveMembers')

                # Pagination TODO: verify this works
                while '@odata.nextLink' in transitive_members:
                    transitive_members += gc.follow_next_link(transitive_members["@odata.nextLink"])

                # TODO: Should we include groups with no members?
                if transitive_members['value']:
                    for member in transitive_members["value"]:
                        if member['@odata.type'] == data_type_group:
                            group_child_info['type'] = "group"
                            group_child_info['displayName'] = member['displayName']
                            group_members.append(group_child_info.copy())

                        if member['@odata.type'] == data_type_user:
                            member_info['type'] = "user"
                            member_info['givenName'] = member['givenName']
                            member_info['surname'] = member['surname']
                            member_info['userPrincipalName'] = member['userPrincipalName']
                            group_members.append(member_info.copy())
                        else:
                            pass

                    # TODO: This copying and clearing of internal data doesn't seem sustainable
                    group_info["members"] = group_members.copy()
                    hierarchy.append(group_info.copy())
                    group_info.clear()
                    group_members.clear()
                    member_info.clear()
                    group_child_info.clear()

        from ...organizations.msgraph_import_actions import perform_msgraph_import
        perform_msgraph_import(hierarchy, self.organization)
