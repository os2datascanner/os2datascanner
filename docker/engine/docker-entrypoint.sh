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

if [ $# -eq 0 ]; then
  echo "No service argument provided!"
  echo "Cannot start unknown service; exiting."
  exit 1
fi

# check if env var $BARE_MODE is set. If yes, don't wait for rabbitMQ
if [[ -z "${BARE_MODE}" ]]; then
  echo "Waiting for rabbitmq"
  python -m os2datascanner.utils.cli wait-for-rabbitmq --wait 30 || exit
  echo "OK"
  echo ""
else
  echo "running in BARE_MODE: ${BARE_MODE}; skipping check for rabbitMQ"
fi

echo "Initialization complete, starting app"

AVAILABLE_STAGES=(explorer processor matcher tagger exporter worker)
# Check if first argument is a stage
if [[ " ${AVAILABLE_STAGES[*]} " =~ $1 ]]; then
  exec python -m "os2datascanner.engine2.pipeline.run_stage" "$@"
else
  exec "$@"
fi
