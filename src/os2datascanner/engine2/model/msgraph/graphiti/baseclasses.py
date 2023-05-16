"""
Base classes for Graphiti.
"""

from abc import ABC, abstractmethod
from enum import Enum


# Base URL for the MS Graph API (without version specifier).
BASE_URL = "https://graph.microsoft.com"


class InvalidMSGraphURLError(BaseException):
    """
    Exception to raise when a user tries to construct
    an invalid query URL for MS Graph.
    """


class GraphNamespace(Enum):
    """
    An enum for 'dotted paths' in the MS Graph
    query URL endpoints (example: 'microsoft.graph.user')
    """
    __BASE = 'microsoft.graph'

    ADMIN = __BASE + '.administrativeUnit'
    APPLICATION = __BASE + '.application'
    GROUP = __BASE + '.group'
    SERVICE_PRINCIPAL = __BASE + '.servicePrincipal'
    USER = __BASE + '.user'


class AbstractGraphNode(ABC):
    """Abstract Base Class for Graph Nodes."""

    @abstractmethod
    def build(self) -> str:
        """Builds and returns the API Endpoint URL as a string."""


class EndpointNode(AbstractGraphNode):
    """Base Class for all Graph endpoints that have a parent node."""

    @abstractmethod
    def parent(self) -> AbstractGraphNode:
        """Returns a reference to the parent node."""
