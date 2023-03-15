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


def sync_all_accounts_and_scanners():
    """To be run after each organizational import job. Synchronizes the
    'covered_accounts' field on scanners to the accounts currently in the
    database."""
    # Avoid circular import

    from os2datascanner.projects.admin.organizations.models import Account

    for account in Account.objects.iterator():
        account.sync_covering_scanners()
