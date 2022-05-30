from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """ BaseSerializer is meant as a parent class.
    It can handle create and update operations on serialized models, but cannot do anything itself.

    Create operations require Meta model field to be set on child class. """

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    def update(self, instance, validated_data):
        interesting_keys = set(self.fields) & set(validated_data.keys())

        for k in interesting_keys:
            setattr(instance, k, validated_data[k])
        if interesting_keys:
            instance.save()

        return instance
