# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
from uuid import uuid4
from rest_framework import serializers
from django.db import models
from os2datascanner.core_organizational_structure.models import Organization as Core_Organization


class Organization(Core_Organization):
    """ Core logic lives in the core_organizational_structure app. """

    uuid = models.UUIDField(
        primary_key=False,
        default=uuid4,
        editable=False,
        verbose_name='UUID',
    )

    @classmethod
    def from_json_object(cls, obj):
        return Organization(
            name=obj["name"],
            uuid=obj["uuid"]
        )


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        exclude = ['id']

    # This field has to be redefined here, because it is read-only on model.
    uuid = serializers.UUIDField()

    # TODO: should the concept of a "Client" also exist in the report module?
    def create(self, validated_data):
        return Organization.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.uuid = validated_data.get('uuid', instance.uuid)
        instance.name = validated_data.get('name', instance.name)
        instance.contact_email = validated_data.get('contact_email', instance.contact_email)
        instance.contact_phone = validated_data.get('contact_phone', instance.contact_phone)

        instance.save()
        return instance
