import logging
import requests
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ...core.models.background_job import BackgroundJob
from ...grants.models import GraphGrant
from os2datascanner.engine2.model.msgraph.utilities import (
        make_token, MSGraphSource)

logger = logging.getLogger(__name__)

# Consider moving GraphCaller out of MSGraphSource.
GraphCaller = MSGraphSource.GraphCaller
# We don't need the MSGraphSource itself here, but GraphCaller is useful
# Deleting MSGraphSource from this module's globals.
del MSGraphSource


class MSGraphImportJob(BackgroundJob):
    grant = models.ForeignKey(GraphGrant, on_delete=models.CASCADE)

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        verbose_name=_('organization'),
        related_name='msimport'
    )

    handled = models.IntegerField(null=True, blank=True)
    to_handle = models.IntegerField(null=True, blank=True)

    def _make_token(self):
        return make_token(
                settings.MSGRAPH_APP_ID,
                self.grant.tenant_id,
                settings.MSGRAPH_CLIENT_SECRET)

    @property
    def progress(self):
        return (self.handled / self.to_handle
                if self.handled is not None and self.to_handle not in (0, None)
                else None)

    @property
    def job_label(self) -> str:
        return "MSGraph Import Job"

    # TODO: Try to bring down complexity.
    def run(self):  # noqa: CCR001, too high cognitive complexity
        data_type_user = "#microsoft.graph.user"
        data_type_group = "#microsoft.graph.group"
        # MSGraph allows constructing select statements as a query parameter, this is a
        # specification of the fields we're interested in.
        graph_select = "?$select="
        graph_select_params = "id, displayName, givenName, surname, " \
                              "mail, userPrincipalName, onPremisesSecurityIdentifier"

        hierarchy = list()
        group_info = dict()
        group_members = list()

        self.status = "Initializing MSGraph AAD Import..."
        self.save()

        with requests.Session() as session:
            gc = GraphCaller(self._make_token, session)
            groups = gc.paginated_get("groups")

            for group in groups:
                uuid = group["id"]  # We absolutely need an id.
                dn = group.get("displayName", "No display name")
                # Store group info in dict
                group_info['uuid'] = uuid
                group_info['name'] = dn

                # Check for transitive members of current group
                transitive_members = gc.paginated_get(
                    f'groups/{uuid}/transitiveMembers{graph_select}{graph_select_params}')

                # TODO: Should we include groups with no members?
                if transitive_members:
                    for member in transitive_members:
                        if member['@odata.type'] == data_type_group:
                            group_members.append({
                                "type": "group",
                                "uuid": member.get("id"),
                                "displayName": (
                                        member.get("displayName")
                                        or "Unnamed group")
                            })

                        if member['@odata.type'] == data_type_user:
                            group_members.append({
                                "type": "user",
                                "uuid": member.get("id"),
                                "givenName": member.get("givenName"),
                                "surname": member.get("surname"),
                                "email": member.get("mail"),
                                "sid": member.get("onPremisesSecurityIdentifier"),
                                "userPrincipalName": member.get(
                                        "userPrincipalName")
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

        # Perform msgraph import runs in a transaction, this means we can't get
        # updates while it runs.
        def _callback(action, *args):
            self.refresh_from_db()
            if action == "group_count":
                count = args[0]
                self.to_handle = count
                self.handled = 0
                self.save()
            elif action == "group_handled":
                group_name = args[0]
                self.handled += 1
                self.status = f"Handled {self.handled}/{self.to_handle} groups \n" \
                              f"Last group handled: {group_name}"
                self.save()

        self.status = "OK.. Data received, build and store relations..."
        self.save()
        perform_msgraph_import(hierarchy, self.organization,
                               progress_callback=_callback)
