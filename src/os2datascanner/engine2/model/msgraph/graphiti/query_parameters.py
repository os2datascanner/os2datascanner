'''
The Microsoft Graph API implements OData Query Parameters:
https://learn.microsoft.com/en-us/graph/query-parameters?tabs=http

This allows the user to perform operations on the query data, server-side.
'''
from .baseclasses import AbstractGraphNode
from .exceptions import DuplicateODataParameterError


class ODataQueryBuilder:
    '''
    Utility class for adding OData Query Parameters to MS Graph API endpoint URLs.
    '''

    def __init__(self):
        self._params = {}

    def build(self, node: AbstractGraphNode) -> str:
        '''
        Builds the complete URL of a node with this objects
        OData Query Parameters.
        '''
        return node.build() + self.to_url()

    def to_url(self) -> str:
        '''
        Converts the internal parameter dict to a well-formatted
        URL.
        '''
        if not self._params:
            return ""

        return "?" + "&".join((f'${k}={v}' for k, v in self._params.items()))

    def count(self, value: bool = True):
        '''
        Sets the "count" OData parameter.
        '''
        if 'count' in self._params:
            raise DuplicateODataParameterError()

        if not isinstance(value, bool):
            raise ValueError()

        self._params['count'] = 'true' if value else 'false'
        return self

    def expand(self, value: str):
        '''
        Sets the "expand" OData parameter.
        '''
        if 'expand' in self._params:
            raise DuplicateODataParameterError()

        self._params['expand'] = value
        return self

    def format(self, value: str = 'json'):
        '''
        Sets the "format" OData parameter.
        '''
        if 'format' in self._params:
            raise DuplicateODataParameterError()

        self._params['format'] = value
        return self

    def search(self, value):
        '''
        Sets the "search" OData parameter.
        '''
        if 'search' in self._params:
            raise DuplicateODataParameterError()

        self._params['search'] = value
        return self

    def select(self, value):
        '''
        Sets the "search" OData parameter.
        '''
        if 'select' in self._params:
            raise DuplicateODataParameterError()

        self._params['select'] = value
        return self

    def top(self, value: int):
        '''
        Sets the "top" OData parameter.
        '''
        if 'top' in self._params:
            raise DuplicateODataParameterError()

        if not isinstance(value, int):
            raise ValueError()

        self._params['top'] = value
        return self

    def remove(self, key):
        '''
        Removes an OData query parameter from the parameter dict.
        Returns a reference to self.
        '''
        if not isinstance(key, str):
            raise ValueError()

        self._params.pop(key)
        return self
