from django.db import transaction
from rest_framework import serializers


class BaseBulkSerializer(serializers.ListSerializer):
    """ Parent class with support for bulk create & bulk update operations. """

    @transaction.atomic
    def create(self, validated_data):
        model = self.Meta.model
        objects = [model(**obj_attrs) for obj_attrs in validated_data]
        return model.objects.bulk_create(objects)

    @transaction.atomic
    def update(self, instances, validated_data):
        # TODO: Perhaps "fields" can be build smarter, in a way where we only look at fields
        # present in the received JSON object.
        model = self.Meta.model
        fields = [field.name for field in model._meta.fields if not field.primary_key]

        for instance, new_data in zip(instances, validated_data):
            for field, value in new_data.items():
                setattr(instance, field, value)

        model.objects.bulk_update(instances, fields)
        return instances
