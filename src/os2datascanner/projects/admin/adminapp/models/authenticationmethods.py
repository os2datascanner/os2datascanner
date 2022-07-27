from django.db import models
from django.utils.translation import ugettext_lazy as _


class AuthenticationMethods(models.Model):

    """Model for keeping """

    methodname = models.CharField(max_length=1024, unique=True,
                                  verbose_name=_('Login method'))
