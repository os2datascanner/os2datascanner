from django.db import models


class MSGraphConfig(models.Model):
    tenant = models.CharField(max_length=100)
