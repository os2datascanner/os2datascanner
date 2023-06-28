from django.shortcuts import get_object_or_404
from django.http import Http404

from ...adminapp.views.views import RestrictedListView
from ..models import OrganizationalUnit, Organization, Account, Position
from ...core.models import Feature, Administrator


class OrganizationalUnitListView(RestrictedListView):
    model = OrganizationalUnit
    context_object_name = 'orgunit_list'
    template_name = 'organizations/orgunit_list.html'
    paginate_by = 10

    # Filter queryset based on organization:
    def get_queryset(self):
        qs = super().get_queryset()

        org = self.kwargs['org']

        qs = qs.filter(organization=org)

        if search_field := self.request.GET.get("search_field", ""):
            qs = qs.filter(name__icontains=search_field)

        show_empty = self.request.GET.get("show_empty", "off") == "on"
        if not show_empty:
            qs = qs.exclude(positions=None)

        return qs

    def setup(self, request, *args, **kwargs):
        org = get_object_or_404(Organization, slug=kwargs['org_slug'])
        kwargs['org'] = org
        if request.user.is_superuser or Administrator.objects.filter(
                user=request.user, client=org.client).exists():
            return super().setup(request, *args, **kwargs)
        else:
            raise Http404(
                "Organization not found."
                )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['organization'] = self.kwargs['org']
        context['accounts'] = Account.objects.filter(organization=self.kwargs['org'])
        context['FEATURES'] = Feature.__members__
        context['search_targets'] = [
            unit.uuid for unit in self.object_list] if self.request.GET.get(
            "search_field", None) else []
        context['show_empty'] = self.request.GET.get('show_empty', 'off') == 'on'
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
