from django.db import models

from ...grants.models import GraphGrant
from .import_service import ImportService
from .exported_mixin import Exported


class MSGraphConfiguration(Exported, ImportService):
    grant = models.ForeignKey(GraphGrant, null=True, on_delete=models.SET_NULL)
