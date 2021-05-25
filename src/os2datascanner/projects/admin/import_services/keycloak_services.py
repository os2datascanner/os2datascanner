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
import json
import requests

from django.conf import settings


# TODO: consider extending this to take list of requests and list of args
def get_token_first(request_function, realm, *args):
    """Utility function to retrieve access token before given API call

    Takes an API request function, a realm pk and the arguments for the given
    request call. Returns the error-response if token retrieval fails. Returns
    the response from the given request call otherwise.
    """
    token_response = request_access_token()
    if token_response.status_code == 200:
        token = token_response.json()['access_token']
        response = request_function(realm, token, *args)
        return response
    else:
        return token_response


# TODO: delete and replace usages with equivalent calls to get_token_first
def create_realm(realm):
    response_token = request_access_token()
    # TODO: add error-handling for unsuccessful requests (here or move all to views?)
    token = response_token.json()['access_token']
    return request_create_new_realm(realm, token)


# TODO: delete and replace usages with equivalent calls to get_token_first
def add_ldap_conf(realm, payload):
    response_token = request_access_token()
    # TODO: add error-handling for unsuccessful requests (here or move all to views?)
    token = response_token.json()['access_token']
    return request_create_component(realm, token, payload)


def request_create_new_realm(realm, token):
    """TODO:"""
    url = f'{settings.KEYCLOAK_BASE_URL}/auth/admin/realms'
    # TODO: consider defining headers as format string?
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
    }
    payload = {
        "enabled": True,
        "id": realm,  # ID equal to name, as per Keycloak Server Admin process
        "realm": realm,
    }
    return requests.post(url, data=json.dumps(payload), headers=headers)


# Simplified while using only one client for admin_module:
# TODO: consider extracting token here? Requires universally valid error handling
def request_access_token():
    """TODO:"""
    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/realms/master/protocol/openid-connect/token')
    payload = {
        'client_id': settings.KEYCLOAK_ADMIN_CLIENT,
        'client_secret': settings.KEYCLOAK_ADMIN_SECRET,
        'grant_type': 'client_credentials',
    }
    return requests.post(url, data=payload)


def request_create_component(realm, token, payload):
    """TODO:"""
    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/components')
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
    }
    return requests.post(url, data=json.dumps(payload), headers=headers)


def request_update_component(realm, token, payload, config_id):
    """TODO:"""
    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/components/{config_id}')
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
    }
    return requests.put(url, data=json.dumps(payload), headers=headers)


def check_ldap_connection(realm, token, connection_url, timeout=5):
    """ Given realm name, token and ldap connection url,
        returns a post request to testLDAPConnection for checking connection"""

    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/testLDAPConnection')

    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
    }
    payload = {
        "action": "testConnection",
        "connectionUrl": connection_url
    }
    data = json.dumps(payload)
    return requests.post(url, data=data, headers=headers, timeout=timeout)


def check_ldap_authentication(realm, token, connection_url,
                              bind_dn, bind_credential, timeout=5):
    """ Given realm name, token, ldap connection url, bindDn and bindCredential,
            returns a post request to testLDAPConnection for checking authentication"""

    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/testLDAPConnection')

    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
    }
    payload = {
        "action": "testAuthentication",
        "connectionUrl": connection_url,
        "bindCredential": bind_credential,
        "bindDn": bind_dn
    }
    data = json.dumps(payload)
    return requests.post(url, data=data, headers=headers, timeout=timeout)


def sync_users(realm, provider_id, token, timeout=5):
    """Given a realm name and token, synchronises that realm's Keycloak users
    with the realm's identity provider."""

    headers = {
        'Authorization': f'bearer {token}'
    }
    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/user-storage/{provider_id}'
           '/sync?action=triggerFullSync')
    return requests.post(url, headers=headers, timeout=timeout)


def get_users(realm, token, timeout=5):
    """Given a realm name and token, returns a list of all the users known to
    Keycloak under that realm."""

    headers = {
        'Authorization': f'bearer {token}'
    }
    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/users')
    return requests.get(url, headers=headers, timeout=timeout)
