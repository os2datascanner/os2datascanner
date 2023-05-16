"""
Graph Nodes related to directory manipulation API.
"""

from .baseclasses import AbstractGraphNode, EndpointNode


class GraphDirectoryNode(EndpointNode):
    """
    Graph Node for the '/directory' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/directory'

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphDirectoryObjectsNode(EndpointNode):
    """
    Graph Node for the '/directoryObjects' endpoint
    """

    def __init__(self, parent: AbstractGraphNode, did=None):
        self._parent = parent
        self._did = did

    def build(self) -> str:
        url = (f'/directoryObjects/{self._did}'
               if self._did else '/directoryObjects')
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphDeletedItemsNode(EndpointNode):
    """
    Graph Node for the '/deletedItems' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, gid=None):
        self._parent = parent
        self._gid = gid

    def build(self) -> str:
        url = (f'/deletedItems/{self._gid}' if self._gid
               else '/deletedItems')
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def restore(self):
        pass
