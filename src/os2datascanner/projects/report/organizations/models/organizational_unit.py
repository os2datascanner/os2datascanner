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
from rest_framework import serializers
from os2datascanner.core_organizational_structure.models import \
    OrganizationalUnit as Core_OrganizationalUnit


class OrganizationalUnit(Core_OrganizationalUnit):
    """ Core logic lives in the core_organizational_structure app.
      Additional logic can be implemented here, but currently, none needed, hence we pass. """
    pass


class OrganizationalUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationalUnit
        fields = '__all__'

    # This field has to be redefined here, because it is read-only on model.
    uuid = serializers.UUIDField()

    def create(self, validated_data):
        return OrganizationalUnit.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.uuid = validated_data.get('pk', instance.uuid)
        instance.name = validated_data.get('name', instance.name)
        instance.parent = validated_data.get('parent', instance.parent)
        instance.organization = validated_data.get('organization', instance.organization)

        instance.save()
        return instance
