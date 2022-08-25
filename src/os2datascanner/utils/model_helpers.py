from django.db import models


class ModelFactory:
    """A ModelFactory is a helper object for Django model classes that
    implements bulk operations with signal-like support for informing clients
    about those operations once they've been performed.

    Clients can indicate their interest in a specific operation by passing a
    callback function to the on_create, on_update and on_delete methods. These
    methods can also be used as decorators.

    A ModelFactory instance is also a Django signal listener, and converts
    post_save and post_delete signals (for model objects that are instances of
    the wrapped class) into calls for its clients."""

    def __init__(self, model):
        self._model = model
        self._on_create = []
        self._on_update = []
        self._on_delete = []

        models.signals.post_save.connect(self._post_save)
        models.signals.post_delete.connect(self._post_delete)

    @property
    def model(self):
        return self._model

    def create(self,
               objects, just_notify=False, **bulk_create_kwargs):
        if not just_notify:
            self.model.objects.bulk_create(objects, **bulk_create_kwargs)
        for callback in self._on_create:
            callback(objects)

    def update(
            self, objects, fields, *, just_notify=False, **bulk_update_kwargs):
        if not fields:
            fields = [field.name for field in self.model._meta.get_fields()]
        if not just_notify:
            self.model.objects.bulk_update(
                    objects, fields, **bulk_update_kwargs)
        for callback in self._on_update:
            callback(objects, fields)

    def delete(self, *objects, just_notify=False):
        if not just_notify:
            objects.delete()
        for callback in self._on_delete:
            callback(objects)

    def on_create(self, func):
        self._on_create.append(func)
        return func

    def on_update(self, func):
        self._on_update.append(func)
        return func

    def on_delete(self, func):
        self._on_delete.append(func)
        return func

    def _post_save(self, *,
                   sender, instance, created, raw, using, update_fields, **kwargs):
        if isinstance(instance, self.model):
            if created:
                self.create([instance], just_notify=True)
            else:
                self.update([instance], update_fields, just_notify=True)

    def _post_delete(self, *,
                     sender, instance, using, **kwargs):
        if isinstance(instance, self.model):
            self.delete([instance], just_notify=True)
