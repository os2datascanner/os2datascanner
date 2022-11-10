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

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Administrator(models.Model):
    """Relates a User to the one Client that they own and manage.

    A User can be an Administrator for at most one Client. Any User who is not
    a superuser will be restricted to interact with their Client only.
    """

    user = models.OneToOneField(
        get_user_model(),
        primary_key=True,
        related_name='administrator_for',
        verbose_name=_('user'),
        on_delete=models.CASCADE,
    )
    client = models.ForeignKey(
        'Client',
        related_name='administrators',
        verbose_name=_('client'),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('administrator')
        verbose_name_plural = _('administrators')

    def __str__(self):
        return f"Administrator: {self.user} (for {self.client})"

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.user} (User) for {self.client} (Client)>"
