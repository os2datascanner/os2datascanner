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
from uuid import uuid4

from django.conf import settings


def create_realm(realm):
    response_token = request_access_token()
    # TODO: add error-handling for unsuccessful requests (here or move all to views?)
    token = response_token.json()['access_token']
    return request_create_new_realm(realm, token)


def add_or_update_ldap_conf(realm, payload):
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


# TODO: check if update is the same url+payload
def request_create_component(realm, token, payload):
    """TODO:"""
    url = (settings.KEYCLOAK_BASE_URL +
           f'/auth/admin/realms/{realm}/components')
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json;charset=utf-8',
    }
    return requests.post(url, data=json.dumps(payload), headers=headers)
