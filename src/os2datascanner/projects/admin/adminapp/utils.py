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
"""Utility methods for the Admin application."""

from typing import NamedTuple

from django.utils import timezone

from .signals import publish_events


def upload_path_webscan_sitemap(instance, filename):
    return "organisation/%s" % instance.organization.slug + "/sitemaps/%s" % filename


def upload_path_gmail_service_account(instance, filename):
    return "organisation/%s" % instance.organization.slug + "/gmail/serviceaccount/%s" % filename


def upload_path_gmail_users(instance, filename):
    return "organisation/%s" % instance.organization.slug + "/gmail/users/%s" % filename


def upload_path_exchange_users(instance, filename):
    return "organisation/%s" % instance.organization.slug + "/mailscan/users/%s" % filename


def upload_path_gdrive_service_account(instance, filename):
    return ("organisation/%s" % instance.organization.slug
            + "/googledrive/serviceaccount/%s" % filename)


def upload_path_gdrive_users(instance, filename):
    return "organisation/%s" % instance.organization.slug + "/googledrive/users/%s" % filename


class CleanMessage(NamedTuple):
    """A CleanMessage conveys a command from the admin module to the report
    module, that DocumentReport objects related to the given account UUIDs and
    scanner pks are to be deleted."""
    time: timezone.datetime = None
    publisher: str = None
    scanners_accounts_dict: dict = None
    event_type = "clean_document_reports"

    def to_json_object(self):
        return {
            "scanners_accounts_dict": self.scanners_accounts_dict,
            "type": self.event_type,
            "time": timezone.datetime.strftime(self.time, "%m/%d/%Y, %H:%M:%S"),
            "publisher": self.publisher
        }

    @staticmethod
    def send(scanners_accounts_dict: dict, publisher="unknown"):
        """Expected structure:
        {
            <scanner_pk_1>: {
                uuids: [
                    <uuid_1>,
                    <uuid_2>
                ],
                usernames: [
                    <username_1>,
                    <username_2>
                ]
            },
            <scanner_pk_2>: {
                uuids: [
                    <uuid_1>,
                    <uuid_3>
                ],
                usernames: [
                    <username_1>,
                    <username_3>
                ]
            }
        }
        """
        message = CleanMessage(
            scanners_accounts_dict=scanners_accounts_dict,
            time=timezone.now(),
            publisher=publisher)
        publish_events([message])

    @staticmethod
    def from_json_object(obj):
        return CleanMessage(
            scanners_accounts_dict=obj.get("scanners_accounts_dict"),
            event_type=obj.get("type"),
            time=timezone.datetime.strptime(obj.get("time"), "%m/%d/%Y, %H:%M:%S"),
            publisher=obj.get("publisher"))
