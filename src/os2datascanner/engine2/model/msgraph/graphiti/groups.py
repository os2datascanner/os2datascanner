"""
Graph Nodes for manipulating groups with relevant API endpoints.
"""

from .baseclasses import AbstractGraphNode, EndpointNode
from .drives import GraphSitesNode


class GraphGroupsNode(EndpointNode):
    """
    Graph Node for the '/groups' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, gid=None):
        self._parent = parent
        self._gid = gid

    def build(self) -> str:
        url = f'/groups/{self._gid}' if self._gid else '/groups'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def conversations(self, cid=None):
        """
        Adds the '/conversations' endpoint to the URL and
        optionally a conversation id if supplied.
        """
        return GraphConversationsNode(self, cid)

    def threads(self, tid=None):
        """
        Adds the '/threads' endpoint to the URL and
        optionally a thread id if supplied.
        """
        return GraphThreadsNode(self, tid)

    def sites(self):
        """
        Adds the '/sites' endpoint to the URL.
        """
        return GraphSitesNode(self)


class GraphConversationsNode(EndpointNode):
    """
    Graph Node for the '/conversations' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, cid=None):
        self._parent = parent
        self._cid = cid

    def build(self) -> str:
        url = (f'/conversations/{self._cid}' if self._cid
               else '/conversations')
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def threads(self, tid=None):
        """
        Adds the '/threads' endpoint to the URL and
        optionally a thread id if supplied.
        """
        return GraphThreadsNode(self, tid)


class GraphThreadsNode(EndpointNode):
    """
    Graph Node for the '/threads' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, tid=None):
        self._parent = parent
        self._tid = tid

    def build(self) -> str:
        url = f'/threads/{self._tid}' if self._tid else '/threads'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def reply(self):
        """
        Adds the '/reply' endpoint to the URL.
        """
        return GraphReplyNode(self)

    def post(self, pid=None):
        """
        Adds the '/post' endpoint to the URL and
        optionally a post id if supplied.
        """
        return GraphPostNode(self, pid)


class GraphReplyNode(EndpointNode):
    """
    Graph Node for the '/reply' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/reply'

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphPostNode(EndpointNode):
    """
    Graph Node for the '/post' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, pid=None):
        self._parent = parent
        self._pid = pid

    def build(self) -> str:
        url = f'/post/{self._pid}' if self._pid else '/post'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent
