'''
'''

from .baseclasses import AbstractGraphNode, EndpointNode
from .extensions import GraphExtensionsNode


class GraphMailFoldersNode(EndpointNode):
    """
    Graph Node for the '/mailFolders' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, mfid=None):
        self._parent = parent
        self._mfid = mfid

    def build(self) -> str:
        url = (f'/mailFolders/{self._mfid}' if self._mfid
               else '/mailFolders')
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def messages(self, mid=None):
        """
        Adds the '/messages' endpoint to the URL and
        optionally a message id if supplied.
        """
        return GraphMessagesNode(self, mid)

    def extensions(self, eid=None):
        """
        Adds the '/extensions' endpoint to the URL and
        optionally an extension id if supplied.
        """
        return GraphExtensionsNode(self, eid)


class GraphMessagesNode(EndpointNode):
    """
    Graph Node for the '/messages' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, mid=None):
        self._parent = parent
        self._mid = mid

    def build(self):
        url = f'/messages/{self._mid}' if self._mid else '/messages'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def attachments(self, aid=None):
        """
        Adds the '/attachments' endpoint to the URL and
        optionally an attachment id if supplied.
        """
        return GraphAttachmentsNode(self, aid)


class GraphAttachmentsNode(EndpointNode):
    """
    Graph Node for the '/attachments' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, aid=None):
        self._parent = parent
        self._aid = aid

    def build(self):
        url = f'/attachments/{self._aid}' if self._aid else '/attachments'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent
