#!/bin/sh
# Copyright (C) 2020 Magenta ApS, http://magenta.dk.
# Contact: info@magenta.dk.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/. */



# This file alters a database users and adds the CREATEDB privilege. It can be
# mounted into the official postgres docker image
# (https://hub.docker.com/_/postgres) at
# `/docker-entrypoint-initdb.d/50-add-createdb-permissions.sh`.
# This is useful to run django test. The testrunner creates a new database
# `test_$DATABASE_NAME` for the duration of the tests. This should not be used
# in production as the normal operation does not require it and we should adhere
# to the principle of least privilege.
add_permission() {
  ENVVAR=$1
  DATABASE_USER=$2

  if [ -z "$DATABASE_USER" ];
  then echo "env var ${ENVVAR} is not set.";
  else

psql <<ENDSQL
ALTER ROLE ${DATABASE_USER} CREATEDB;
ENDSQL
fi
}

add_permission \$ADMIN_DATABASE_USER "${ADMIN_DATABASE_USER}"
add_permission \$REPORT_DATABASE_USER "${REPORT_DATABASE_USER}"
