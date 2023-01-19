from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView

from ..models import OrganizationalUnit, Organization, Account, Position


class OrganizationalUnitListView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    context_object_name = 'orgunit_list'
    template_name = 'organizations/orgunit_list.html'

    # Filter queryset based on organization:
    def get_queryset(self):
        org = self.kwargs['org']
        search_field = self.request.GET.get("search_field", "")
        units = OrganizationalUnit.objects.filter(
            organization=org, name__icontains=search_field).prefetch_related("positions")

        show_empty = self.request.GET.get("show_empty", "off") == "on"
        if not show_empty:
            units = units.exclude(positions=None)

        return units

    def setup(self, request, *args, **kwargs):
        org = get_object_or_404(Organization, slug=kwargs['org_slug'])
        kwargs['org'] = org
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.kwargs['org']
        context['accounts'] = Account.objects.filter(organization=self.kwargs['org'])
        return context

    def post(self, request, *args, **kwargs):

        if new_manager_uuid := request.POST.get("add-manager", None):
            orgunit = OrganizationalUnit.objects.get(pk=request.POST.get("orgunit"))
            new_manager = Account.objects.get(uuid=new_manager_uuid)
            Position.objects.get_or_create(account=new_manager, unit=orgunit, role="manager")

        elif rem_manager_uuid := request.POST.get("rem-manager", None):
            print("HIT")
            orgunit = OrganizationalUnit.objects.get(pk=request.POST.get("orgunit"))
            rem_manager = Account.objects.get(uuid=rem_manager_uuid)
            Position.objects.filter(account=rem_manager, unit=orgunit, role="manager").delete()

        print(request.POST)

        response = self.get(request, *args, **kwargs)

        return response
