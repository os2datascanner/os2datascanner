# Copyright (C) 2021 Magenta ApS, http://magenta.dk.
# Contact: info@magenta.dk.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

################################################################################
# Changes to this file requires approval from Labs. Please add a person from   #
# Labs as required approval to your MR if you have any changes.                #
################################################################################

FROM python:3.6 AS application

LABEL org.opencontainers.image.title="OS2datascanner - API" \
      org.opencontainers.image.vendor="Magenta ApS" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.url="https://os2datascanner.magenta.dk/" \
      org.opencontainers.image.documentation="https://os2datascanner.readthedocs.io/en/latest/" \
      org.opencontainers.image.source="https://github.com/os2datascanner/os2datascanner"

# Force the stdout and stderr streams from python to be unbuffered. See
# https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED=1 \
  OS2DS_SERVER_SYSTEM_CONFIG_PATH=/code/docker/docker-settings.toml \
  OS2DS_SERVER_USER_CONFIG_PATH=/user-settings.toml \
  PYTHONPATH=/code/src/:$PYTHONPATH

# Install system depedencies
WORKDIR /code/requirements/sys-requirements
COPY requirements/sys-requirements/sys-requirements-common.txt \
     requirements/sys-requirements/sys-requirements-engine.txt \
     ./

# hadolint ignore=DL3008,SC2046
RUN set -ex \
  # Add an image specific group and user.
  # Note: this is a system user/group, but have
  # UID/GID above the normal SYS_UID_MAX/SYS_GID_MAX of 999, but also above the
  # automatic ranges of UID_MAX/GID_MAX used by useradd/groupadd.
  # Hopefully there will be no conflicts with users of the
  # host system or users of other docker containers.
  && groupadd -g 73050 -r os2ds_api\
  && useradd -u 73050 --no-log-init -r -g os2ds_api os2ds_api \
  # Install system dependencies from file.
  && apt-get -y update \
  && apt-get -y install --no-install-recommends $(grep -oh '^[^#][[:alnum:].-]*' sys-requirements*.txt) \
  # clean up after apt-get and man-pages
  && apt-get clean && rm -rf "/var/lib/apt/lists/*" "/tmp/*" "/var/tmp/*" "/usr/share/man/??" "/usr/share/man/??_*"

# Install python requirements
WORKDIR /code/requirements/python-requirements
COPY requirements/python-requirements/requirements-api.txt \
     requirements/python-requirements/requirements-test.txt \
     requirements/python-requirements/requirements-lint.txt \
     ./
# hadolint ignore=DL4006
RUN find requirements*.txt -print0 | xargs -0 -n1 pip install -r

WORKDIR /code/docker/
COPY docker/api/docker-settings.toml ./docker-settings.toml
COPY docker/api/gunicorn-settings.py ./gunicorn-settings.py

WORKDIR /code/src/os2datascanner
COPY src/os2datascanner/server ./server/
COPY src/os2datascanner/engine2 ./engine2/
COPY src/os2datascanner/utils ./utils
COPY src/os2datascanner/__init__.py ./

WORKDIR /code
COPY VERSION ./
COPY LICENSE ./
COPY README.rst ./
COPY NEWS.rst ./

WORKDIR /code/src/os2datascanner/server
USER os2ds_api:os2ds_api
EXPOSE 5000

CMD ["gunicorn", \
     "--config", "/code/docker/gunicorn-settings.py", \
     "os2datascanner.server.wsgi"]
