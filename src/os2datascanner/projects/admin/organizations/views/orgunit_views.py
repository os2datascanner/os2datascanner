from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView

from ..models import OrganizationalUnit, Organization


class OrganizationalUnitListView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    context_object_name = 'orgunit_list'
    template_name = 'organizations/orgunit_list.html'

    # Filter queryset based on organization:
    def get_queryset(self):
        top_unit = self.kwargs['org'].top_unit
        if not top_unit:
            return OrganizationalUnit.objects.none()
        else:
            return top_unit.get_descendants(include_self=True)

    def setup(self, request, *args, **kwargs):
        org = get_object_or_404(Organization, slug=kwargs['org_slug'])
        kwargs['org'] = org
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.kwargs['org']
        return context
