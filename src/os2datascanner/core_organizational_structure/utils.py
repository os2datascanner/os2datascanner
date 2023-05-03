from django.core.exceptions import ImproperlyConfigured


def get_serializer(model_class):
    """
    Return the serializer class that corresponds to the given model class.
    """
    serializer_class = getattr(model_class, 'serializer_class', None)
    if not serializer_class:
        raise ImproperlyConfigured(
            f"No serializer found for {model_class.__name__}. "
            "Please define a serializer for this model."
        )
    return serializer_class
