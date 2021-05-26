from .utilities.results import SingleResult


__converters = {}


def conversion(output_type, *mime_types):
    """Decorator: registers the decorated function as the converter of each of
    the specified MIME types to the specified OutputType."""
    def _conversion(f):
        def _register_converter(output_type, mime_type):
            k = (output_type, mime_type)
            if k in __converters:
                raise ValueError(
                        "BUG: can't register two handlers for"
                        " the same (OutputType, MIME type) pair!", k)
            else:
                __converters[k] = f
        if mime_types:
            for m in mime_types:
                _register_converter(output_type, m)
        else:
            _register_converter(output_type, None)
        return f
    return _conversion


def convert(resource, output_type, mime_override=None) -> SingleResult:
    """Tries to convert a Resource to the specified OutputType by using the
    database of registered conversion functions.

    Raises a KeyError if no conversion exists."""
    mime_type = resource.compute_type() if not mime_override else mime_override
    try:
        converter = __converters[(output_type, mime_type)]
    except KeyError as e:
        try:
            converter = __converters[(output_type, None)]
        except KeyError:
            # Raise the original, more specific, exception
            raise KeyError("No converters registered for "
                           "{0}".format(e)) from  e
    value = converter(resource)
    if value is not None and not isinstance(value, SingleResult):
        value = SingleResult(None, output_type, value)
    return value
