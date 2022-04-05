from django.db import models
from .import_service import ImportService
from .exported_mixin import Exported


class MSGraphConfiguration(Exported, ImportService):
    tenant_id = models.CharField(max_length=256, verbose_name="Tenant ID",
                                 null=False)
