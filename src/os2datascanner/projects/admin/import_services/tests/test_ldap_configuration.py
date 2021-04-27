import json
from unittest import skip

from django.test import TestCase
from django.utils.timezone import now

from os2datascanner.projects.admin.core.models import Client
from os2datascanner.projects.admin.organizations.models import Organization

from ..models import Realm, LDAPConfig


class LDAPConfigTest(TestCase):

    def setUp(self) -> None:
        self.client = Client.objects.create(
            name="TestClient",
            contact_email="test@magenta.dk",
            contact_phone="12345678"
        )
        self.organization = Organization.objects.create(
            # uuid is specified to ensure same uuid in expected json
            uuid="3d6d288f-b75f-43e2-be33-a43803cd1243",
            name="TestOrg", slug="test_org", client=self.client,
        )
        self.realm = Realm.objects.create(
            realm_id=self.organization.slug,
            organization=self.organization,
            last_modified=now(),
        )

    def test_payload(self):
        config = LDAPConfig.objects.create(
            organization=self.organization,
            vendor="other",
            username_attribute="cn",
            rdn_attribute="cn",
            uuid_attribute="uidNumber",
            user_obj_classes="inetOrgPerson, organizationalPerson",
            connection_protocol="ldap://",
            connection_url="ldap_server:389",
            users_dn="ou=TestUnit,dc=magenta,dc=test",
            search_scope=2,
            bind_dn="cn=admin,dc=magenta,dc=test",
            last_modified=now(),
        )
        config.ldap_credential = "testMAG"
        expected_json = '{"name": "ldap", "providerId": "ldap", "providerType": "org.keycloak.storage.UserStorageProvider", "parentId": "test_org", "id": "3d6d288f-b75f-43e2-be33-a43803cd1243", "config": {"enabled": ["true"], "priority": ["0"], "fullSyncPeriod": ["-1"], "changedSyncPeriod": ["-1"], "cachePolicy": ["DEFAULT"], "evictionDay": [], "evictionHour": [], "evictionMinute": [], "maxLifespan": [], "batchSizeForSync": ["1000"], "editMode": ["READ_ONLY"], "importEnabled": ["true"], "syncRegistrations": ["false"], "vendor": ["other"], "usePasswordModifyExtendedOp": [], "usernameLDAPAttribute": ["cn"], "rdnLDAPAttribute": ["cn"], "uuidLDAPAttribute": ["uidNumber"], "userObjectClasses": ["inetOrgPerson, organizationalPerson"], "connectionUrl": ["ldap://ldap_server:389"], "usersDn": ["ou=TestUnit,dc=magenta,dc=test"], "authType": ["simple"], "startTls": [], "bindDn": ["cn=admin,dc=magenta,dc=test"], "bindCredential": ["testMAG"], "customUserSearchFilter": [], "searchScope": ["2"], "validatePasswordPolicy": ["false"], "trustEmail": ["false"], "useTruststoreSpi": ["ldapsOnly"], "connectionPooling": ["true"], "connectionPoolingAuthentication": [], "connectionPoolingDebug": [], "connectionPoolingInitSize": [], "connectionPoolingMaxSize": [], "connectionPoolingPrefSize": [], "connectionPoolingProtocol": [], "connectionPoolingTimeout": [], "connectionTimeout": [], "readTimeout": [], "pagination": ["true"], "allowKerberosAuthentication": ["false"], "serverPrincipal": [], "keyTab": [], "kerberosRealm": [], "debug": ["false"], "useKerberosForPasswordAuthentication": ["false"]}}'
        self.assertEqual(json.dumps(config.get_payload_dict()), expected_json)
