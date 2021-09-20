from rest_framework import serializers
from ..organizations.models import OrganizationalUnit

class OrganizationalUnitSerializer(serializers.ModelSerializer):
	class Meta:
		model = OrganizationalUnit
		fields = ('uuid', 'name', 'lft', 'rght', 'tree_id', 'level', 'parent', 'organization')