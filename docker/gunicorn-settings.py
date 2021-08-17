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
import os


bind = "0.0.0.0:5000"
workers = os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1)
worker_class = "uvicorn.workers.UvicornWorker"

# default directory for heartbeat file is in /tmp, which in some Linux distros
# is stored in memory via tmpfs filesystem. Docker containers, however, do not
# have /tmp on tmpfs by default - so we use /dev/shm
# https://pythonspeed.com/articles/gunicorn-in-docker/
worker_tmp_dir = "/dev/shm" 

accesslog = "-"
errorlog = "-"
capture_output = True
