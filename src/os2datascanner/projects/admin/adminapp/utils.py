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
"""Utility methods for the OS2Webscanner project."""

import os
import shutil
import requests
import chardet
import logging
import pathlib
import typing

from django.db import IntegrityError
from django.conf import settings


def capitalize_first(s):
    """Capitalize the first letter of a string, leaving the others alone."""
    if s is None or len(s) < 1:
        return ""
    return s.replace(s[0], s[0].upper(), 1)


def get_failing_urls(scan_id, target_directory):
    """Retrieve the physical document that caused conversion errors."""
    source_file = os.path.join(
            settings.VAR_DIR,
            "logs/scans/occurrence_{0}.log".format(scan_id)
            )
    with open(source_file, "r") as f:
        lines = f.readlines()

    urls = [l.split("URL: ")[1].strip() for l in lines if l.find("URL") >= 0]

    for u in set(urls):
        f = requests.get(u, stream=True)
        target = os.path.join(
                target_directory,
                u.split('/')[-1].split('#')[0].split('?')[0]
                )
        with open(target, 'wb') as local_file:
            shutil.copyfileobj(f.raw, local_file)


def get_codec_and_string(bytestring, encoding="utf-8"):
    """ Get actual encoding and stringdata from bytestring
        use UnicodeDammit if this  doesn't work
        https://www.crummy.com/software/BeautifulSoup/bs4/doc/#unicode-dammit
    """ 
    try:
        stringdata = bytestring.decode(encoding)
    except AttributeError:
        # no decode - is a string
        return None, bytestring
    except UnicodeDecodeError:
        encoding = chardet.detect(bytestring).get('encoding')
        if encoding is not None:
            stringdata = bytestring.decode(encoding)
        else:
            raise

    return encoding, stringdata


def secure_save(object):
    try:
       object.save()
    except IntegrityError as ie:
       logging.error('Error Happened: {}'.format(ie))


def domain_form_manipulate(form):
    """ Manipulates domain form fields.
    All form widgets will have added the css class 'form-control'.
    """
    for fname in form.fields:
        f = form.fields[fname]
        f.widget.attrs['class'] = 'form-control'

    return form


def as_file_uri(path: typing.Union[str, pathlib.Path]) -> str:
    # TODO: consolidate with `scrapy-webscanner/utils.py`
    if isinstance(path, str) and path.startswith('file://'):
        return path
    elif not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    return path.as_uri()


def upload_path_webscan_sitemap(instance, filename):
    return "organisation/%s" % instance.ldap_organization.slug + "/sitemaps/%s" % filename


def upload_path_gmail_service_account(instance, filename):
    return "organisation/%s" % instance.ldap_organization.slug + "/gmail/serviceaccount/%s" % filename


def upload_path_gmail_users(instance, filename):
    return "organisation/%s" % instance.ldap_organization.slug + "/gmail/users/%s" % filename


def upload_path_exchange_users(instance, filename):
    return "organisation/%s" % instance.ldap_organization.slug + "/mailscan/users/%s" % filename


def upload_path_gdrive_service_account(instance, filename):
    return "organisation/%s" % instance.ldap_organization.slug + "/googledrive/serviceaccount/%s" % filename


def upload_path_gdrive_users(instance, filename):
    return "organisation/%s" % instance.ldap_organization.slug + "/googledrive/users/%s" % filename
