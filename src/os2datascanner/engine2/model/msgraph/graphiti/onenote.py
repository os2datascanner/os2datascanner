"""
"""

from .baseclasses import AbstractGraphNode, EndpointNode


class GraphOnenoteNode(EndpointNode):
    """
    Graph Node for the '/onenote' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/onenote'

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def notebook(self, nid=None):
        '''
        Adds the "/notebook" endpoint to the URL and
        optionally a notebook id if supplied.
        '''
        return GraphNotebookNode(self, nid)


class GraphNotebookNode(EndpointNode):
    """
    Graph Node for the '/notebook' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, nid=None):
        self._parent = parent
        self._nid = nid

    def build(self) -> str:
        url = f'/notebook/{self._nid}' if self._nid else '/notebook'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent
