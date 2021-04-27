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
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from .exported_mixin import Exported
from .import_service import ImportService
from .realm import Realm
from ...adminapp.aescipher import encrypt, decrypt  # Suggestion: move to core?


# NOTE: all help-texts are copied from the equivalent form in Keycloak admin
class LDAPConfig(Exported, ImportService):
    vendor = models.CharField(
        max_length=32,
        choices=[
            ('ad', _('Active Directory')),
            ('other', _('other').capitalize()),
        ],
        verbose_name=_('vendor'),
    )
    username_attribute = models.CharField(
        max_length=64,
        help_text=_(
            "Name of LDAP attribute, which is mapped as username. "
            "For many LDAP server vendors it can be 'uid'. "
            "For Active Directory it can be 'sAMAccountName' or 'cn'. "
            "The attribute should be filled for all LDAP user records you "
            "want to import from LDAP."
        ),
        verbose_name=_('username LDAP attribute'),
    )
    rdn_attribute = models.CharField(
        max_length=64,
        help_text=_(
            "Name of LDAP attribute, which is used as RDN of typical user DN. "
            "Usually, but not necessarily, the same as username LDAP attribute."
            " For example for Active Directory, it is common to use 'cn' as "
            "RDN attribute when username attribute might be 'sAMAccountName'."
        ),
        verbose_name=_('RDN LDAP attribute'),
    )
    uuid_attribute = models.CharField(
        max_length=64,
        help_text=_(
            "Name of LDAP attribute, which is used as unique object identifier "
            "(UUID) for objects in LDAP. For many LDAP server vendors, "
            "it is 'entryUUID'; however some are different. "
            "For example for Active Directory it should be 'objectGUID'. "
            "If your LDAP server does not support the notion of UUID, "
            "you can use any other attribute that is supposed to be unique "
            "among LDAP users in the tree. For example 'uid' or 'entryDN'."
        ),
        verbose_name=_('UUID LDAP attribute'),
    )
    user_obj_classes = models.TextField(
        help_text=_(
            "All values of LDAP objectClass attribute for users in LDAP "
            "divided by comma. For example: "
            "'inetOrgPerson, organizationalPerson'. "
            "User records are only imported if they have all those classes."
        ),
        verbose_name=_('user object classes'),
    )
    connection_protocol = models.CharField(
        max_length=8,
        choices=(('ldap://', 'ldap'), ('ldaps://', 'ldaps')),
        default='ldaps://',
        help_text=_(
            "Choose between an encrypted connection protocol (ldaps) or an "
            "unencrypted one (ldap). Only select the unencrypted protocol if "
            "absolutely necessary."
        ),
        verbose_name=_('connection protocol'),
    )
    connection_url = models.CharField(
        max_length=256,
        help_text=_(
            "Connection URL to the LDAP server. "
        ),
        verbose_name=_('connection URL'),
    )
    users_dn = models.TextField(
        help_text=_(
            "Distinguished name for the (top) OU in which to search for users."
        ),
        verbose_name=_('DN for users (OU)'),
    )
    search_scope = models.PositiveSmallIntegerField(
        choices=(
            (1, _('one level').capitalize()),
            (2, _('subtree').capitalize()),
        ),
        help_text=_(
            "For one level, the search applies only for users in the DNs "
            "specified by User DNs. "
            "For subtree, the search applies to the whole subtree. "
            "See LDAP documentation for more details."
        ),
        verbose_name=_('search scope'),
    )
    bind_dn = models.TextField(
        help_text=_(
            "Distinguished name for the service account allowing access to LDAP"
        ),
        verbose_name=_('LDAP service account user name'),
    )
    # Initialization vector for decryption
    _iv_ldap_credential = models.BinaryField(
        db_column='iv_ldap',
        max_length=32,
        blank=True,
        null=False,
        verbose_name='initialization vector for ldap credential',
    )
    # Encrypted credential
    _cipher_ldap_credential = models.BinaryField(
        db_column='cipher_ldap',
        max_length=1024,
        blank=True,
        null=False,
        verbose_name='cipher text for ldap credential',
    )

    @property
    def ldap_credential(self):
        return decrypt(self._iv_ldap_credential,
                       bytes(self._cipher_ldap_credential))

    @ldap_credential.setter
    def ldap_credential(self, value):
        self._iv_ldap_credential, self._cipher_ldap_credential = encrypt(value)

    class Meta:
        verbose_name = _('LDAP configuration')
        verbose_name_plural = _('LDAP configurations')

    def get_payload_dict(self):
        realm = get_object_or_404(Realm, organization_id=self.pk)
        full_connection_url = self.connection_protocol + self.connection_url
        return {
            "name": "ldap",
            "providerId": "ldap",
            "providerType": "org.keycloak.storage.UserStorageProvider",
            "parentId": realm.pk,
            "id": str(self.pk),
            "config": {
                "enabled": ["true"],
                "priority": ["0"],
                "fullSyncPeriod": ["-1"],
                "changedSyncPeriod": ["-1"],
                "cachePolicy": ["DEFAULT"],
                "evictionDay": [],
                "evictionHour": [],
                "evictionMinute": [],
                "maxLifespan": [],
                "batchSizeForSync": ["1000"],
                "editMode": ['READ_ONLY'],
                "importEnabled": ["true"],
                "syncRegistrations": ["false"],
                "vendor": [self.vendor],
                "usePasswordModifyExtendedOp": [],
                "usernameLDAPAttribute": [self.username_attribute],
                "rdnLDAPAttribute": [self.rdn_attribute],
                "uuidLDAPAttribute": [self.uuid_attribute],
                "userObjectClasses": [self.user_obj_classes],
                "connectionUrl": [full_connection_url],
                "usersDn": [self.users_dn],
                "authType": ["simple"],
                "startTls": [],
                "bindDn": [self.bind_dn],
                "bindCredential": [self.ldap_credential],
                "customUserSearchFilter": [],
                "searchScope": [str(self.search_scope)],
                "validatePasswordPolicy": ["false"],
                "trustEmail": ["false"],
                "useTruststoreSpi": ["ldapsOnly"],
                "connectionPooling": ["true"],
                "connectionPoolingAuthentication": [],
                "connectionPoolingDebug": [],
                "connectionPoolingInitSize": [],
                "connectionPoolingMaxSize": [],
                "connectionPoolingPrefSize": [],
                "connectionPoolingProtocol": [],
                "connectionPoolingTimeout": [],
                "connectionTimeout": [],
                "readTimeout": [],
                "pagination": ["true"],
                "allowKerberosAuthentication": ["false"],
                "serverPrincipal": [],
                "keyTab": [],
                "kerberosRealm": [],
                "debug": ["false"],
                "useKerberosForPasswordAuthentication": ["false"]
            }
        }
