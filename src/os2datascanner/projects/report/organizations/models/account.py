# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2datascanner is developed by Magenta in collaboration with the OS2 public
# sector open source network <https://os2.eu/>.
#
import os
import logging

from PIL import Image

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from os2datascanner.core_organizational_structure.models import Account as Core_Account
from os2datascanner.utils.system_utilities import time_now
from rest_framework import serializers

from ..serializer import BaseSerializer

logger = logging.getLogger(__name__)


class Account(Core_Account):
    """ Core logic lives in the core_organizational_structure app.
    Additional logic can be implemented here, but currently, none needed, hence we pass. """

    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='account',
        verbose_name=_('User'),
        null=True, blank=True)
    last_handle = models.DateTimeField(
        verbose_name=_('Last handle'),
        null=True,
        blank=True)
    _image = models.ImageField(
        upload_to="media/images",
        default=None,
        null=True,
        blank=True,
        verbose_name=_('image'))

    def update_last_handle(self):
        self.last_handle = time_now()
        self.save()

    @property
    def time_since_last_handle(self):
        """Return time since last handled, if the user has handled something.
        If not, return 3 days to trigger a warning to the user."""
        return (time_now() - self.last_handle).total_seconds() if self.last_handle else 60*60*24*3

    @property
    def image(self):
        return os.path.join(settings.MEDIA_ROOT, self._image.url) if self._image else None


@receiver(post_save, sender=Account)
def resize_image(sender, **kwargs):
    size = (300, 300)
    try:
        with Image.open(kwargs["instance"]._image.path) as image:
            image.thumbnail(size, Image.ANTIALIAS)
            image.save(kwargs["instance"]._image.path, optimize=True)
    except ValueError:
        logger.debug("image resize failed", exc_info=True)


class AccountSerializer(BaseSerializer):
    class Meta:
        model = Account
        fields = '__all__'

    # This field has to be redefined here, cause it is read-only on model.
    uuid = serializers.UUIDField()
