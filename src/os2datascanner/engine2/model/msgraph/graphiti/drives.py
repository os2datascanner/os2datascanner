from .baseclasses import AbstractGraphNode, EndpointNode


class GraphDriveNode(EndpointNode):
    """
    Graph Node for the '/drive' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/drive'

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def items(self, iid=None):
        """
        Adds the '/items' endpoint to the URL and
        optionally a item id if supplied.
        """
        return GraphItemsNode(self, iid)


class GraphDrivesNode(EndpointNode):
    """
    Graph Node for the '/drives' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, did=None):
        self._parent = parent
        self._did = did

    def build(self) -> str:
        url = f'/drives/{self._did}' if self._did else '/drives'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def items(self, iid=None):
        """
        Adds the '/items' endpoint to the URL and
        optionally a item id if supplied.
        """
        return GraphItemsNode(self, iid)

    def root(self):
        """
        Adds the '/directory' endpoint to the URL.
        """
        return GraphRootNode(self)


class GraphItemsNode(EndpointNode):
    """
    Graph Node for the '/items' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode, iid=None):
        self._parent = parent
        self._iid = iid

    def build(self) -> str:
        url = f'/items/{self._iid}' if self._iid else '/items'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphRootNode(EndpointNode):
    """
    Graph Node for the '/root' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/root'

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphBundlesNode(EndpointNode):
    """
    Graph Node for the '/bundles' endpoint
    """

    def __init__(self, parent: AbstractGraphNode, did=None):
        self._parent = parent
        self._did = did

    def build(self) -> str:
        url = f'/bundles/{self._did}' if self._did else '/bundles'
        return self.parent().build() + url

    def parent(self) -> AbstractGraphNode:
        return self._parent


class GraphListNode(EndpointNode):
    """
    Graph Node for the '/list' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/list'

    def items(self, iid=None):
        """
        Adds the '/items' endpoint to the URL and
        optionally a item id if supplied.
        """
        return GraphItemsNode(self, iid)

    def drive(self):
        """
        Adds the '/drive' endpoint to the URL.
        """
        return GraphDriveNode(self)


class GraphSitesNode(EndpointNode):
    """
    Graph Node for the '/sites' endpoint.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/sites'

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def root(self):
        """
        Adds the '/root' endpoint to the URL.
        """
        return GraphRootNode(self)
