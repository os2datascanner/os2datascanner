#!/bin/bash
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

set -e


# check if env var $BARE_MODE is set. If yes, don't wait for services
if [[ -z "${BARE_MODE}" ]]; then
  # Ensure db is up
  echo "Waiting for db to be ready"
  python manage.py waitdb --wait 30 || exit
  echo "OK"
  echo ""

  # Wait for rabbitmq to start
  echo "Waiting for rabbitmq"
  python -m os2datascanner.utils.cli wait-for-rabbitmq || exit
  echo "OK"
  echo ""
else
  echo "running in BARE_MODE: ${BARE_MODE}; skipping check for DB/rabbitMQ"
fi

if [ -z "${OS2DS_SKIP_DJANGO_MIGRATIONS}" ]; then
  # Run Migrate
  python manage.py migrate
else
  echo "OS2DS_SKIP_DJANGO_MIGRATIONS set: ${OS2DS_SKIP_DJANGO_MIGRATIONS}"
  echo "Skipping automatic migrations"
fi

echo "Initialization complete, starting app"
exec "$@"
