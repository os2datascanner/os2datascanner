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
from os2datascanner.core_organizational_structure.models import Organization as Core_Organization
from os2datascanner.core_organizational_structure.models import \
    OrganizationSerializer as Core_OrganizationSerializer
from ..seralizer import BaseBulkSerializer


class Organization(Core_Organization):
    """ Core logic lives in the core_organizational_structure app. """
    serializer_class = None


class OrganizationBulkSerializer(BaseBulkSerializer):
    """ Bulk create & update logic lives in BaseBulkSerializer """

    class Meta:
        model = Organization


class OrganizationSerializer(Core_OrganizationSerializer):
    pk = serializers.UUIDField(read_only=False)

    class Meta(Core_OrganizationSerializer.Meta):
        model = Organization
        list_serializer_class = OrganizationBulkSerializer


Organization.serializer_class = OrganizationSerializer
