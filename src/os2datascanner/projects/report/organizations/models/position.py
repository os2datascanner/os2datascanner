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
from os2datascanner.core_organizational_structure.models import Position as Core_Position


class Position(Core_Position):
    """ Core logic lives in the core_organizational_structure app.
      Additional logic can be implemented here, but currently, none needed, hence we pass. """
    pass


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'

    # This field has to be redefined here, because it is read-only on model.
    pk = serializers.IntegerField()

    def create(self, validated_data):
        return Position.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.account = validated_data.get('account', instance.account)
        instance.unit = validated_data.get('unit', instance.unit)
        instance.role = validated_data.get('role', instance.role)

        instance.save()
        return instance
