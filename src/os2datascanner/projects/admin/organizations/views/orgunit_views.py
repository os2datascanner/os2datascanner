from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from django.db.models import Q

from ..models import OrganizationalUnit, Organization, Account, Position
from ...core.models.client import Feature


class OrganizationalUnitListView(LoginRequiredMixin, ListView):
    model = OrganizationalUnit
    context_object_name = 'orgunit_list'
    template_name = 'organizations/orgunit_list.html'
    paginate_by = 10

    # Filter queryset based on organization:
    def get_queryset(self):
        org = self.kwargs['org']

        parent_query = Q(parent__isnull=True, organization=org)

        is_htmx = self.request.headers.get("HX-Request", False)
        if is_htmx:
            htmx_trigger = self.request.headers.get("HX-Trigger-Name", None)
            if htmx_trigger == "children":
                parent_query = Q(parent__pk=self.request.GET.get("parent"), organization=org)

        if search_field := self.request.GET.get("search_field", ""):
            parent_query = Q(name__icontains=search_field, organization=org)

        units = OrganizationalUnit.objects.filter(parent_query)

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
        context['FEATURES'] = Feature.__members__
        context['search_targets'] = [
            unit.uuid for unit in self.object_list] if self.request.GET.get(
            "search_field", None) else []
        return context

    def post(self, request, *args, **kwargs):

        if new_manager_uuid := request.POST.get("add-manager", None):
            orgunit = OrganizationalUnit.objects.get(pk=request.POST.get("orgunit"))
            new_manager = Account.objects.get(uuid=new_manager_uuid)
            Position.objects.get_or_create(account=new_manager, unit=orgunit, role="manager")

        if rem_manager_uuid := request.POST.get("rem-manager", None):
            orgunit = OrganizationalUnit.objects.get(pk=request.POST.get("orgunit"))
            rem_manager = Account.objects.get(uuid=rem_manager_uuid)
            Position.objects.filter(account=rem_manager, unit=orgunit, role="manager").delete()

        response = self.get(request, *args, **kwargs)

        return response
