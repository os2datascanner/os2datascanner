from .baseclasses import AbstractGraphNode, EndpointNode


class GraphDeltaNode(EndpointNode):
    """
    Graph Node for the '/delta' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/delta'

    def parent(self) -> AbstractGraphNode:
        return self._parent
