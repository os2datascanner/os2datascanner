"""
Graph Nodes and endpoints related to users (including '/me').
"""

from .baseclasses import AbstractGraphNode, EndpointNode
from .calendars import (GraphCalendarNode, GraphCalendarsNode,
                        GraphCalendarGroupsNode, GraphCalendarViewNode,
                        GraphEventsNode)
from .delta import GraphDeltaNode
from .drives import GraphDriveNode, GraphDrivesNode
from .mails import GraphMailFoldersNode
from .onenote import GraphOnenoteNode


class GraphMeNode(EndpointNode):
    """
    Graph Node for the '/me' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/me'

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def change_password(self):
        """
        Adds the '/changePassword' endpoint to the URL.
        """
        return GraphChangePasswordNode(self)

    def app_role_assignments(self):
        """
        Adds the '/appRoleAssignments' endpoint to the URL.
        """
        return GraphAppRoleAssignmentsNode(self)

    def calendar(self):
        """
        Adds the '/calendar' endpoint to the URL.
        """
        return GraphCalendarNode(self)

    def calendar_groups(self, cgid=None):
        """
        Adds the '/calendarGroups' endpoint to the URL and
        optionally a 'calendar_group_id' if supplied.
        """
        return GraphCalendarGroupsNode(self, cgid)

    def calendars(self, cid=None):
        """
        Adds the '/calendars' endpoint to the URL and
        optionally a 'calendar_id' if supplied.
        """
        return GraphCalendarsNode(self, cid)

    def calendar_view(self, eid=None):
        """
        Adds the '/calendarView' endpoint to the URL and
        optionally a 'event_id' if supplied.
        """
        return GraphCalendarViewNode(self, eid)

    def drive(self):
        """
        Adds the '/drive' endpoint to the URL.
        """
        return GraphDriveNode(self)

    def drives(self, did=None):
        """
        Adds the '/drives' endpoint to the URL and
        optionally a 'drive_id' if supplied.
        """
        return GraphDrivesNode(self, did)

    def events(self, eid=None):
        """
        Adds the '/events' endpoint to the URL and
        optionally a 'event_id' if supplied.
        """
        return GraphEventsNode(self, eid)

    def mail_folders(self, mfid=None):
        """
        Adds the '/mailFolders' endpoint to the URL and
        optionally a 'mailFolder_id' if supplied.
        """
        return GraphMailFoldersNode(mfid)

    def onenote(self):
        """
        Adds the '/onenote' endpoint to the URL.
        """
        return GraphOnenoteNode(self)


class GraphUsersNode(EndpointNode):
    """
    Graph Node for the '/users' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, uid=None):
        self._parent = parent
        self._uid = uid

    def build(self) -> str:
        url = f'/users/{self._uid}' if self._uid else '/users'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def delta(self):
        """
        Adds the '/delta' endpoint to the URL.
        """
        return GraphDeltaNode(self)

    def app_role_assignments(self, uid=None):
        """
        Adds the '/appRoleAssignments' endpoint to the URL and
        optionally a user id or 'userPrincipalName'.
        """
        return GraphAppRoleAssignmentsNode(self, uid)

    def change_password(self):
        """
        Adds the '/changePassword' endpoint to the URL.
        """
        return GraphChangePasswordNode(self)

    def calendar(self):
        """
        Adds the '/calendar' endpoint to the URL.
        """
        return GraphCalendarNode(self)

    def calendar_groups(self, gid=None):
        """
        Adds the '/calendarGroups' endpoint to the URL and
        optionally a 'calendar_group_id' if supplied.
        """
        return GraphCalendarGroupsNode(self, gid)

    def calendars(self, cid=None):
        """
        Adds the '/calendars' endpoint to the URL and
        optionally a 'calendar_id' if supplied.
        """
        return GraphCalendarsNode(self, cid)

    def calendar_view(self, eid=None):
        """
        Adds the '/calendarView' endpoint to the URL and
        optionally a 'event_id' if supplied.
        """
        return GraphCalendarViewNode(self, eid)

    def drive(self):
        """
        Adds the '/drive' endpoint to the URL.
        """
        return GraphDriveNode(self)

    def drives(self, did=None):
        """
        Adds the '/drives' endpoint to the URL and
        optionally a 'drive_id' if supplied.
        """
        return GraphDrivesNode(self, did)

    def events(self, eid=None):
        """
        Adds the '/events' endpoint to the URL and
        optionally a 'event_id' if supplied.
        """
        return GraphEventsNode(self, eid)

    def mail_folders(self, mfid=None):
        """
        Adds the '/mailFolders' endpoint to the URL and
        optionally a 'mailFolder_id' if supplied.
        """
        return GraphMailFoldersNode(self, mfid)

    def onenote(self):
        """
        Adds the '/onenote' endpoint to the URL.
        """
        return GraphOnenoteNode(self)


class GraphChangePasswordNode(EndpointNode):
    """
    Graph Node for the '/changePassword' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/changePassword'

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphAppRoleAssignmentsNode(EndpointNode):
    """
    Graph Node for the '/appRoleAssignments' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, uid=None):
        self._parent = parent
        self._uid = uid

    def build(self) -> str:
        url = (f'/appRoleAssignments/{self._uid}' if self._uid
               else '/appRoleAssignments')
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent
