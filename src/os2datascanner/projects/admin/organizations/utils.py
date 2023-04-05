from django.apps import apps
from os2datascanner.utils.system_utilities import time_now

from os2datascanner.core_organizational_structure.utils import get_serializer
from ..organizations.models.broadcasted_mixin import Broadcasted
from ..organizations.models.organization import Organization


def get_broadcasted_models():
    """Returns a list of all models (except Organization) that inherit from Broadcasted."""
    models = []
    for model in apps.get_models():
        # We'll only want Organization included in create.
        # Deleting an Org from the report module potentially destroys too much.
        # (Document reports)
        if issubclass(model, Broadcasted) and model is not Organization:
            models.append(model)
    return models


def group_into(collection, *models, key=lambda o: o):
    """Collects a heterogeneous sequence of Django model objects into subsets
    of the same type, and yields each model manager and (non-empty) collection
    in the model order specified.

    The input collection does not need to contain Django model objects, as long
    as an appropriate key function is provided to select such an object from
    each item in the collection."""
    if collection:
        for subset in models:
            manager = subset.objects

            instances = [k for k in collection if isinstance(key(k), subset)]
            if instances:
                yield (manager, instances)


def set_imported_fields(model_objects: list):
    """Takes a list of model objects, iterates and updates model fields
    that stem from the Imported model class."""
    now = time_now()
    for o in model_objects:
        # TODO: import_requested should perhaps be background job creation time.
        o.imported = True
        o.last_import = now
        o.last_import_requested = now


def save_and_serializer(manager, instances):
    """Provided a model manager and a list of serialized instances,
     bulk creates and returns instances in a serialized fashion."""
    serializer = get_serializer(manager.model)
    manager.bulk_create(instances)
    if hasattr(manager, "rebuild"):
        manager.rebuild()
    return serializer(instances, many=True).data


def update_and_serialize(manager, instances):
    properties = set()
    serializer = get_serializer(manager.model)
    for _, props in instances:
        properties |= set(props)

    # We'll only want to send one update instruction pr. object.
    unique_instances = set(obj for obj, _ in instances)
    manager.bulk_update(unique_instances, properties)

    return serializer(unique_instances, many=True).data


def delete_and_listify(manager, instances):
    deletion_pks = [str(i.pk) for i in instances]
    qs = manager.filter(pk__in=deletion_pks)
    # It seems like there is no good way to avoid signals to be sent for every deleted object.
    # A slightly hacky workaround is to use raw_delete, but this CAN potentially break, as it is
    # using the private API.
    # Old ongoing ticket: https://code.djangoproject.com/ticket/9519
    qs._raw_delete(qs.db)
    return deletion_pks
