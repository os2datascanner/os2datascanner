#!/bin/sh
# Copyright (C) 2020 Magenta ApS, http://magenta.dk.
# Contact: info@magenta.dk.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

################################################################################
# Changes to this file requires approval from Labs. Please add a person from   #
# Labs as required approval to your MR if you have any changes.                #
################################################################################

# This file creates a database user for the report module.
# It can be mounted into the official
# postgres docker image (https://hub.docker.com/_/postgres) at
# `/docker-entrypoint-initdb.d/40-create-report-db-and-user.sh`. This is preferable to
# using the POSTGRES_* env variables as this user is not a SUPERUSER. A
# SUPERUSER can be used as privilege escalation to the postgres service system
# user in the event of SQL injection.

if [ -n "$REPORT_DATABASE_USER" ];
then
  true "${REPORT_DATABASE_PASSWORD:?ERROR! REPORT_DATABASE_PASSWORD is unset.}"
  true "${REPORT_DATABASE_NAME:?ERROR! REPORT_DATABASE_NAME is unset.}"

# Intentionally not indented due to the way psql parses the statements.
psql -v ON_ERROR_STOP=1 <<ENDSQL
CREATE DATABASE ${REPORT_DATABASE_NAME};
CREATE USER ${REPORT_DATABASE_USER} WITH ENCRYPTED PASSWORD '${REPORT_DATABASE_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${REPORT_DATABASE_NAME} TO ${REPORT_DATABASE_USER};
ENDSQL
fi
