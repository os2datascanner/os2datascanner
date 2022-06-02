from django import template
from ..models.organizational_unit import OrganizationalUnit

register = template.Library()


@register.filter
def get_orgunit_list(self):
    top_unit = OrganizationalUnit.objects.filter(organization=self, parent=None)

    if not top_unit:
        return OrganizationalUnit.objects.none()
    else:
        return top_unit.get_descendants(include_self=True)
