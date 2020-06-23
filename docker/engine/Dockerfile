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

FROM python:3.6 AS engine

LABEL org.opencontainers.image.title="OS2datascanner - Engine" \
      org.opencontainers.image.vendor="Magenta ApS" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.url="https://os2datascanner.magenta.dk/" \
      org.opencontainers.image.documentation="https://os2datascanner.readthedocs.io/en/latest/" \
      org.opencontainers.image.source="https://github.com/os2datascanner/os2datascanner"

# Force the stdout and stderr streams from python to be unbuffered. See
# https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED=1 \
  DSC_ENGINE_SYSTEM_CONFIG_PATH=/code/docker/docker-settings.toml \
  DSC_ENGINE_USER_CONFIG_PATH=/user-settings.toml \
  PYTHONPATH=/code/src/:$PYTHONPATH

# Ensure system user and install system depedencies
WORKDIR /code/requirements/sys-requirements
COPY requirements/sys-requirements/sys-requirements-common.txt \
     requirements/sys-requirements/sys-requirements-engine.txt \
     ./
RUN cat sys-requirements-*.txt > sys-requirements.txt
RUN set -ex \
  # Add an image specific group and user.
  # Note: this is a system user/group, but have
  # UID/GID above the normal SYS_UID_MAX/SYS_GID_MAX of 999, but also above the
  # automatic ranges of UID_MAX/GID_MAX used by useradd/groupadd.
  # Hopefully there will be no conflicts with users of the
  # host system or users of other docker containers.
  && groupadd -g 73030 -r os2ds_engine\
  && useradd -u 73030 --no-log-init -r -g os2ds_engine os2ds_engine \
  # Install system dependencies from file.
  && apt-get -y update \
  && apt-get -y install --no-install-recommends $(grep -o '^[^#][[:alnum:].-]*' sys-requirements.txt) \
  # clean up after apt-get and man-pages
  && apt-get clean && rm -rf "/var/lib/apt/lists/*" "/tmp/*" "/var/tmp/*" "/usr/share/man/??" "/usr/share/man/??_*"

# Install python requirements
WORKDIR /code/requirements/python-requirements
COPY requirements/python-requirements/requirements-engine.txt \
     requirements/python-requirements/requirements-test.txt \
     requirements/python-requirements/requirements-lint.txt \
     ./
RUN pip install \
    -r requirements-engine.txt \
    -r requirements-test.txt \
    -r requirements-lint.txt

# Copy code
WORKDIR /code/src/os2datascanner
COPY src/os2datascanner/engine2 ./engine2/
COPY src/os2datascanner/tests ./tests
COPY src/os2datascanner/utils ./utils
COPY src/os2datascanner/__init__.py ./
COPY VERSION .
COPY LICENSE .
COPY README .
COPY NEWS.rst .

COPY docker/engine/docker-entrypoint.sh /code/docker/docker-entrypoint.sh

# Set up to run given command as the new user
USER os2ds_engine:os2ds_engine

ENV AVAILABLE_STAGES="explorer,processor,matcher,tagger,exporter"

ENTRYPOINT ["/code/docker/docker-entrypoint.sh"]
CMD ["explorer", "-h"]
