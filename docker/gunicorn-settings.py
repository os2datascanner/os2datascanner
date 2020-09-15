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


# Settings for gunicorn in docker.
import multiprocessing


bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
accesslog =  "/log/access.log"
worker_tmp_dir = "/dev/shm"
