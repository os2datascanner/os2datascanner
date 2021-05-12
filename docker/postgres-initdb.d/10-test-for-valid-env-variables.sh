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

# This file checks that a user is set for at least one of the modules.
# Checks for necessary variable for each of the modules are delegated to
# their respective scripts.

EITHER_EXISTS="${ADMIN_DATABASE_USER:-$REPORT_DATABASE_USER}"
true "${EITHER_EXISTS:?ERROR! At least one of ADMIN_DATABASE_USER and REPORT_DATABASE_USER must be provided.}"
