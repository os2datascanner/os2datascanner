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
from uuid import uuid4

from django.db import models
from django.utils.translation import ugettext_lazy as _

from ...adminapp.aescipher import encrypt, decrypt  # Suggestion: move to core?


class KeycloakServer(models.Model):
    """TODO:"""
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name=_('UUID'),
    )
    url = models.URLField(
        verbose_name=_('server URL'),
    )

    # TODO: Consider need for specific clients (we currently use one universally)?
    #        if so: add requests for client settings AND retrieval of secret
    #       NB! client refers to a client in Keycloak, NOT a core.Client instance in the datascanner system
    # Initialization vector for decryption
    _iv = models.BinaryField(
        db_column='iv',
        max_length=32,
        blank=True,
        null=False,
        verbose_name='initialization vector',
    )

    # Encrypted secret
    _ciphertext = models.BinaryField(
        db_column='ciphertext',
        max_length=1024,
        blank=True,
        null=False,
        verbose_name='cipher text',
    )

    @property
    def secret(self):
        return decrypt(self._iv, bytes(self._ciphertext))

    @secret.setter
    def secret(self, value):
        self._iv, self._ciphertext = encrypt(value)

    class Meta:
        verbose_name = _('Keycloak server')
        verbose_name_plural = _('Keycloak servers')
