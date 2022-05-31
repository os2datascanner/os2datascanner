from django.db import models
from django.utils.translation import ugettext_lazy as _

from ..aescipher import encrypt, decrypt
from .authenticationmethods_model import AuthenticationMethods


class Authentication(models.Model):

    """Model for keeping authentication information."""

    # User login for websites, network drives etc.
    username = models.CharField(max_length=1024, unique=False, blank=True, default='',
                                verbose_name=_('Brugernavn'))

    # One of the two encryption keys for decrypting the password
    iv = models.BinaryField(max_length=32, unique=False, blank=True,
                            verbose_name=_('Initialization Vector'))

    # The encrypted password
    ciphertext = models.BinaryField(max_length=1024, unique=False, blank=True,
                                    verbose_name='Password')

    domain = models.CharField(max_length=2024, unique=False, blank=True, default='',
                              verbose_name=_('User domain'))

    models.ForeignKey(AuthenticationMethods,
                      null=True,
                      related_name='authentication_method',
                      verbose_name=_('Login method'),
                      on_delete=models.CASCADE)

    def get_password(self):
        return decrypt(bytes(self.iv), bytes(self.ciphertext))

    def set_password(self, password, key=None):
        self.iv, self.ciphertext = encrypt(password, key)

    def __str__(self):
        if self.domain:
            return '{}@{}'.format(self.username, self.domain)
        else:
            return self.username
