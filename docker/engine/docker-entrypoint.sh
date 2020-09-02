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

AVAILABLE_STAGES=$(echo $AVAILABLE_STAGES | tr "," "\n")

# Check if first argument is a stage
if [[ " ${AVAILABLE_STAGES[@]} " =~ "$1" ]]; then

  STAGE=$1

  # ${@:2} adds all arguments except the first one (which is the stage)
  exec python -m "os2datascanner.engine2.pipeline.${STAGE}" "${@:2}"
else
  exec "$@"
fi
