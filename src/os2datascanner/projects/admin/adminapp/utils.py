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
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

"""Utility methods for the OS2Webscanner project."""

import os
import shutil
import requests
import time
import datetime
import chardet
import logging
import pathlib
import typing

from django.db import IntegrityError
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader

from .models.scannerjobs.webscanner_model import WebScanner


def capitalize_first(s):
    """Capitalize the first letter of a string, leaving the others alone."""
    if s is None or len(s) < 1:
        return ""
    return s.replace(s[0], s[0].upper(), 1)


def get_supported_rpc_params():
    """Return a list of supported Scanner parameters for the RPC interface."""
    return ["do_cpr_scan", "do_cpr_modulus11",
            "do_cpr_ignore_irrelevant", "do_ocr", "do_name_scan",
            "output_spreadsheet_file", "do_cpr_replace", "cpr_replace_text",
            "do_name_replace", "name_replace_text", "do_address_scan",
            "do_address_replace", "address_replace_text", "columns"]


def do_scan(user, urls, params={}, blocking=False, visible=False):
    """Create a scanner to scan a list of URLs.

    The 'urls' parameter may be either http:// or file:// URLS - we expect the
    scanner to handle this distinction transparently. The list is assumed to be
    well-formed and denote existing files/URLs. The consequences of load errors
    etc. should be in the report.

    The 'params' parameter should be a dict of supported Scanner
    parameters and values. Defaults are used for unspecified parameters.
    """
    scanner = WebScanner()
    scanner.organization = user.profile.organization

    scanner.name = user.username + '-' + str(time.time())
    scanner.do_run_synchronously = True
    # TODO: filescan does not contain these properties.
    scanner.do_last_modified_check = False
    scanner.do_last_modified_check_head_request = False
    scanner.process_urls = urls
    scanner.is_visible = visible

    supported_params = get_supported_rpc_params()
    for param in params:
        if param in supported_params:
            setattr(scanner, param, params[param])
        else:
            raise ValueError("Unsupported parameter passed: " + param +
                             ". Supported parameters: " +
                             str(supported_params))

    scanner.save()

    scan = scanner.run('xmlrpc', user=user, blocking=blocking)
    # NOTE: Running scan may have failed.
    # Pass the error message or empty scan in that case.

    return scan


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
