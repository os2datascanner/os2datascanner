"""
Custom Exceptions for error handling in graphiti.
"""


class InvalidMSGraphURLError(BaseException):
    '''
    Exception for indicating that a URL points to an
    invalid endpoint when trying to build the URL string.
    '''


class DuplicateODataParameterError(BaseException):
    '''
    Exception for handling cases where a user tries to add the
    same OData Query Parameter Twice.
    '''
