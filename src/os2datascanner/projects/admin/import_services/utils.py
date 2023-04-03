#!/usr/bin/env python
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
# OS2datascanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (https://os2.eu/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( https://os2.eu/ )

import structlog

from django.shortcuts import get_object_or_404
from django.conf import settings

from os2datascanner.projects.admin.core.models.background_job import JobState
from os2datascanner.projects.admin.import_services.models import (LDAPConfig,
                                                                  Realm,
                                                                  LDAPImportJob,
                                                                  MSGraphImportJob,
                                                                  OS2moImportJob)
from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner import Scanner
from os2datascanner.projects.admin.adminapp.utils import CleanMessage
from .models.msgraph_configuration import MSGraphConfiguration
from .models.os2mo_configuration import OS2moConfiguration


logger = structlog.get_logger(__name__)


def start_ldap_import(ldap_conf: LDAPConfig):
    """
    LDAP import jobs are allowed to be created if latest import job has finished.
    """
    # if no organization return 404
    realm = get_object_or_404(Realm, organization_id=ldap_conf.pk)

    # get latest import job
    latest_importjob = realm.importjob.first()
    if not latest_importjob \
            or latest_importjob.exec_state == JobState.FINISHED \
            or latest_importjob.exec_state == JobState.FAILED \
            or latest_importjob.exec_state == JobState.CANCELLED:
        LDAPImportJob.objects.create(
            realm=realm
        )
        logger.info(f"Import job created for LDAPConfig {ldap_conf.pk}")
    else:
        logger.info("LDAP import is not possible right now for "
                    f"LDAPConfig {ldap_conf.pk}")


def start_msgraph_import(msgraph_conf: MSGraphConfiguration):
    """
    MS Graph Import Job start utility. MS Graph Import Jobs can only be
    created if no other jobs are running.
    """

    try:
        latest_importjob = MSGraphImportJob.objects.filter(
            grant=msgraph_conf.grant
        ).latest('created_at')

        if latest_importjob.exec_state == JobState.FINISHED \
                or latest_importjob.exec_state == JobState.FAILED \
                or latest_importjob.exec_state == JobState.CANCELLED:
            MSGraphImportJob.objects.create(
                grant=msgraph_conf.grant,
                organization=msgraph_conf.organization,
            )
            logger.info(f"Import job created for MSGraphConfiguration {msgraph_conf.pk}")

        else:
            logger.info("MS Graph import is not possible right now for "
                        f"MSGraphConfiguration {msgraph_conf.pk}")

    except MSGraphImportJob.DoesNotExist:
        MSGraphImportJob.objects.create(
            grant=msgraph_conf.grant,
            organization=msgraph_conf.organization,
        )
        logger.info(f"Import job created for MSGraphConfiguration {msgraph_conf.pk}")


def start_os2mo_import(os2mo_conf: OS2moConfiguration):
    """
    OS2mo Import Job start utility. OS2mo Import Jobs can only be
    created if no other jobs are running.
    """

    try:
        latest_importjob = OS2moImportJob.objects.filter(
            organization=os2mo_conf.organization
        ).latest('created_at')

        if latest_importjob.exec_state == JobState.RUNNING or \
                latest_importjob.exec_state == JobState.WAITING:
            logger.info("OS2mo import is not possible right now for "
                        f"OS2mo import {os2mo_conf.pk}")
        else:
            OS2moImportJob.objects.create(
                organization=os2mo_conf.organization,
            )
            logger.info(f"Import job created for OS2moConfiguration {os2mo_conf.pk}")

    except OS2moImportJob.DoesNotExist:
        OS2moImportJob.objects.create(
            organization=os2mo_conf.organization,
        )
        logger.info(f"Import job created for OS2moConfiguration {os2mo_conf.pk}")


def construct_dict_from_scanners_stale_accounts() -> dict:
    """Returns a dict in the correct configuration for packaging in a
    CleanMessage:
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
    all_scanners = Scanner.objects.all()
    scanners_accounts_dict = {}

    for scanner in all_scanners:
        if scanner.statuses.last() and not scanner.statuses.last().finished:
            logger.info(f"Scanner “{scanner.name}” is currently running.")
        else:
            stale_accounts = scanner.get_stale_accounts()

            if stale_accounts:

                usernames = [account.username for account in stale_accounts]

                logger.info(
                    f"Cleaning up accounts: {', '.join(usernames)} for scanner: {scanner}.")

                scanners_accounts_dict[scanner.pk] = {
                    "uuids": [str(account.uuid) for account in stale_accounts],
                    "usernames": usernames
                }

    return scanners_accounts_dict


def post_import_cleanup() -> None:
    """If the AUTOMATIC_IMPORT_CLEANUP-setting is enabled, this function
    initiates cleanup of all accounts, which will no longer be covered by
    future scans, but have been in the past."""

    if settings.AUTOMATIC_IMPORT_CLEANUP:

        logger.info("Performing post import cleanup...")

        scanners_accounts_dict = construct_dict_from_scanners_stale_accounts()

        CleanMessage.send(scanners_accounts_dict, publisher="post_import")

        logger.info("Post import cleanup message sent to report module!")
