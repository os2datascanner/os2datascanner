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

set -ex

# TODO: Uncomment when the management command has been added
# ./manage.py ensure_db_connection --wait 30

# Run Migrate
./manage.py migrate

# Generate static content
# TODO: determine if we need this
# ./manage.py collectstatic --no-input --clear

exec "$@"
