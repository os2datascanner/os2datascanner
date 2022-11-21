"""
Utilities for building MS Graph query URLs.
"""
from urllib.parse import urlsplit

from .baseclasses import (BASE_URL,
                          AbstractGraphNode, EndpointNode)
from .exceptions import InvalidMSGraphURLError
from .directory import GraphDirectoryNode, GraphDirectoryObjectsNode
from .drives import GraphDriveNode, GraphDrivesNode, GraphSitesNode
from .groups import GraphGroupsNode
from .users import GraphMeNode, GraphUsersNode


class MSGraphURLBuilder(AbstractGraphNode):
    """
    URL Builder utility for MS Graph Query URLs.
    """

    def __init__(self, url=BASE_URL):
        self._url = url

    def build(self) -> str:
        """
        Build and return the URL constructed so far.
        """
        return self._url

    @staticmethod
    def from_url(url) -> AbstractGraphNode:
        """
        Converts a raw URL to a URL builder instance.

        If the supplied URL is not a valid MS Graph
        query an InvalidMSGraphURLError is raised.
        """
        scheme, netloc, path, _ = urlsplit(url)
        base = scheme + '://' + netloc

        if base != BASE_URL:
            raise InvalidMSGraphURLError(
                f"Cannot parse URL: {url} - invalid base: {base}, expected: {BASE_URL}")

        url_builder = MSGraphURLBuilder()

        for endpoint in path.split('/'):
            try:
                add_endpoint = getattr(url_builder, endpoint)
                add_endpoint()
            except AttributeError as exc:
                raise InvalidMSGraphURLError(
                    "Cannot parse URL: {url} - invalid endpoint: {endpoint}"
                    ) from exc

        return url_builder

    def v1(self):
        """
        Adds the '/v1.0' (stable) endpoint to the URL.
        """
        return GraphV1Node(self)

    def beta(self):
        """
        Adds the '/beta' endpoint to the URL.
        """
        return GraphBetaNode(self)


class GraphV1Node(EndpointNode):
    """
    Endpoint for stable (v1.0) version of MS Graph API.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/v1.0'

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def me(self):
        """
        Adds the '/me' endpoint to the URL.
        Note that this URL is only valid in certain
        settings.
        """
        return GraphMeNode(self)

    def users(self, user_id=None):
        """
        Adds the '/users' endpoint to the URL and
        optionally a user id or 'userPrincipalName'
        if supplied.
        """
        return GraphUsersNode(self, user_id)

    def directory_objects(self, did=None):
        """
        Adds the '/directoryObjects' endpoint to the URL and
        optionally a directory id if supplied.
        """
        return GraphDirectoryObjectsNode(self, did)

    def directory(self):
        """
        Adds the '/directory' endpoint to the URL.
        """
        return GraphDirectoryNode(self)

    def drive(self):
        """
        Adds the '/drive' endpoint to the URL.
        """
        return GraphDriveNode(self)

    def drives(self, did=None):
        """
        Adds the '/drives' endpoint to the URL and
        optionally a directory id if supplied.
        """
        return GraphDrivesNode(self, did)

    def groups(self, gid=None):
        """
        Adds the '/groups' endpoint to the URL and
        optionally a group id if supplied.
        """
        return GraphGroupsNode(self, gid)

    def sites(self):
        """
        Adds the '/sites' endpoint to the URL.
        """
        return GraphSitesNode(self)


class GraphBetaNode(EndpointNode):
    """
    Endpoint for beta version of MS Graph API.
    """

    def __init__(self, parent: AbstractGraphNode):
        self._parent = parent

    def build(self) -> str:
        return self.parent().build() + '/beta'

    def parent(self) -> AbstractGraphNode:
        return self._parent

    def me(self):
        """
        Adds the '/me' endpoint to the URL.
        Note that this URL is only valid in certain
        settings.
        """
        return GraphMeNode(self)

    def users(self, user_id=None):
        """
        Adds the '/users' endpoint to the URL and
        optionally a user id or 'userPrincipalName'
        if supplied.
        """
        return GraphUsersNode(self, user_id)

    def drive(self):
        """
        Adds the '/drive' endpoint to the URL.
        """
        return GraphDriveNode(self)

    def drives(self, did=None):
        """
        Adds the '/drives' endpoint to the URL and
        optionally a directory id if supplied.
        """
        return GraphDrivesNode(self, did)

    def groups(self, gid=None):
        """
        Adds the '/groups' endpoint to the URL and
        optionally a group id if supplied.
        """
        return GraphGroupsNode(self, gid)

    def sites(self):
        """
        Adds the '/sites' endpoint to the URL.
        """
        return GraphSitesNode(self)
