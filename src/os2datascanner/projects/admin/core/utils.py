from ..organizations.models import Organization
from .models import Client
from ..import_services.models.import_service import ImportService


def clear_import_services(client: Client):
    organizations = Organization.objects.filter(client=client)

    for org in organizations:
        import_services = ImportService.objects.filter(organization=org)
        import_services.delete()
