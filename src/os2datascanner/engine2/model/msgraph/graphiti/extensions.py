"""
"""

from .baseclasses import AbstractGraphNode, EndpointNode


class GraphExtensionsNode(EndpointNode):
    """
    Graph Node for the '/extensions' endpoint
    """

    def __init__(self, parent: AbstractGraphNode, eid=None):
        self._parent = parent
        self._eid = eid

    def build(self) -> str:
        url = (f'/extensions/{self._eid}' if self._eid
               else '/extensions')
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent
