from .baseclasses import AbstractGraphNode, EndpointNode


class GraphCalendarNode(EndpointNode):
    """
    Graph Node for the '/calendar' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/calendar'

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphCalendarsNode(EndpointNode):
    """
    Graph Node for the '/calendars' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, cid=None):
        self._parent = parent
        self._cid = cid

    def build(self) -> str:
        url = f'/calendars/{self._cid}' if self._cid else '/calendars'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphCalendarGroupsNode(EndpointNode):
    """
    Graph Node for the '/calendarGroups' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, cgid=None):
        self._parent = parent
        self._cgid = cgid

    def build(self) -> str:
        url = f'/calendarGroups/{self._cgid}' if self._cgid else '/calendarGroups'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def calendars(self, cid=None):
        """
        Adds the '/calendars' endpoint to the URL and
        optionally a calendarGroup id if supplied.
        """
        return GraphCalendarsNode(self, cid)


class GraphCalendarViewNode(EndpointNode):
    """
    Graph Node for the '/calendarView' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, eid=None):
        self._parent = parent
        self._eid = eid

    def build(self) -> str:
        url = f'/calendarView/{self._eid}' if self._eid else '/calendarView'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphEventsNode(EndpointNode):
    """
    Graph Node for the '/events' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, eid=None):
        self._parent = parent
        self._eid = eid

    def build(self) -> str:
        url = f'/events/{self._eid}' if self._eid else '/events'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent
