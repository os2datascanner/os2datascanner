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

from os2datascanner.projects.admin.core.models.background_job import JobState
from os2datascanner.projects.admin.import_services.models import (LDAPConfig,
                                                                  Realm,
                                                                  ImportJob,
                                                                  MSGraphImportJob)
from .models.msgraph_configuration import MSGraphConfiguration

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
        ImportJob.objects.create(
            realm=realm
        )
        logger.info(f"Import job created for LDAPConfig {ldap_conf.pk}")
    else:
        logger.info("LDAP import is not possible right now for "
                    f"LDAPConfig {ldap_conf.pk}")


def start_msgraph_import(msgraph_conf: MSGraphConfiguration):
    """"""
    MSGraphImportJob.objects.create(
        tenant_id=msgraph_conf.tenant_id,
        organization=msgraph_conf.organization,
    )
    logger.info(f"Import job created for MSGraphConfiguration {msgraph_conf.pk}")
