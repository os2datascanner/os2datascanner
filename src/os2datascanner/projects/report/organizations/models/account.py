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

from os2datascanner.core_organizational_structure.models import Account as Core_Account
from rest_framework import serializers


class Account(Core_Account):
    """ Core logic lives in the core_organizational_structure app.
    Additional logic can be implemented here, but currently, none needed, hence we pass. """
    pass


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

    # This field has to be redefined here, cause it is read-only on model.
    uuid = serializers.UUIDField()

    def create(self, validated_data):
        return Account.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.uuid = validated_data.get('uuid', instance.uuid)
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.organization = validated_data.get('organization', instance.organization)

        instance.save()
        return instance
