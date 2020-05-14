#!/bin/sh
# Copyright (C) 2019 Magenta ApS, http://magenta.dk.
# Contact: info@magenta.dk.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

################################################################################
# Changes to this file requires approval from Labs. Please add a person from   #
# Labs as required approval to your MR if you have any changes.                #
################################################################################

# This file creates a database user. It can be mounted into the official
# postgres docker image (https://hub.docker.com/_/postgres) at
# `/docker-entrypoint-initdb.d/20-create-db-and-user.sh`. This is preferable to
# using the POSTGRES_* env variables as this user is not a SUPERUSER. A
# SUPERUSER can be used as privilege escalation to the postgres service system
# user in the event of SQL injection.

true "${DATABASE_USER:?DATABASE_USER is unset. Error.}"
true "${DATABASE_PASSWORD:?DATABASE_PASSWORD is unset. Error.}"
true "${DATABASE_NAME:?DATABASE_NAME is unset. Error.}"

psql -v ON_ERROR_STOP=1 <<ENDSQL
CREATE DATABASE ${DATABASE_NAME};
CREATE USER ${DATABASE_USER} WITH ENCRYPTED PASSWORD '${DATABASE_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${DATABASE_NAME} TO ${DATABASE_USER};
ENDSQL
