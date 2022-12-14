class UnknownSchemeError(LookupError):
    """When Source.from_url does not know how to handle a given URL, either
    because no Source subclass is registered as a handler for its scheme or
    because the URL is not valid, an UnknownSchemeError will be raised.
    Its only associated value is a string identifying the scheme, if one was
    present in the URL.

    An UnknownSchemeError can also be raised by the JSON deserialisation code
    if no handler exists for an object's type label; in these circumstances,
    the single associated value is the type label."""


class DeserialisationError(KeyError):
    """When converting a JSON representation of an object back into an object,
    if a required property is missing or has a nonsensical value, a
    DeserialisationError will be raised. It has two associated values: the
    type of object being deserialised, if known, and the property at issue."""


class ModelException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
        for arg in args:
            if not isinstance(arg, (str, int,)):
                raise Exception("Prohibited exception type")

    @property
    def server(self):
        return self.args[0]


class UncontactableError(ModelException):
    """If a remote server cannot be contacted, or is out of reach, this
    exception should be used to notify the user in human-readable
    language."""


class UnauthorisedError(ModelException):
    """If a remote server is contactable, yet refuses to receive proper
    authentication, this exception should be used to notify the user in
    human-readable language."""


class UnavailableError(ModelException):
    """If a remote server is contactable, receives authentication, yet the
    desired resource still doesn't exist, this exception should be used to
    notify the user in human-readable language."""
