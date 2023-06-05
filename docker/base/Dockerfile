# Copyright (C) 2020 Magenta ApS, http://magenta.dk.
# Contact: info@magenta.dk.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Need to specify this at the top or else Docker will be confused
ARG BASE_IMAGE=base

FROM node:15 AS frontend

WORKDIR /code/src/os2datascanner/projects

COPY --chown=node:node src/os2datascanner/projects/static ./static
RUN npm ci --prefix static; \

# Build production bundle
# NB! Doesn't start a webserver, only bundles files!
    npm run prod --prefix static

USER node

# Build development bundle
# NB! Watches for changes, so no automatic exit!
CMD ["npm", "run", "dev", "--prefix", "static"]

FROM python:3.11.3 AS base

# Force the stdout and stderr streams from python to be unbuffered. See
# https://docs.python.org/3/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED=1 \
  PYTHONPATH=/code/src/:$PYTHONPATH

# Ensure system user and install system depedencies
WORKDIR /code/requirements
COPY requirements/sys-requirements/sys-requirements-all.txt \
     requirements/sys-requirements/backport-sys-requirements.txt \
     ./sys-requirements/

COPY requirements/python-requirements/requirements-all.txt \
     ./python-requirements/

ARG SUPERCRONIC_VERSION=v0.1.12
ARG SUPERCRONIC_SHA1SUM=048b95b48b708983effb2e5c935a1ef8483d9e3e

# hadolint ignore=DL3008,SC2046,DL4006
RUN set -ex \
  # We need LibreOffice 7.2 or higher, but this is not easily available through Debian \
  # Use a backport repo to achieve this.
  && echo "deb https://deb.debian.org/debian bullseye-backports main contrib non-free \
  deb-src https://deb.debian.org/debian bullseye-backports main contrib non-free" >> /etc/apt/sources.list \
  # Install system dependencies from file.
  && apt-get -y update \
  && apt-get -y install --no-install-recommends $(grep -oh '^[^#][[:alnum:].-]*' sys-requirements/sys-requirements*.txt) \
  # Install from backport file too.
  && apt-get -y -t bullseye-backports install --no-install-recommends $(grep -oh '^[^#][[:alnum:].-]*' sys-requirements/backport-sys-requirements.txt) \
  # clean up after apt-get and man-pages
  && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/man/?? /usr/share/man/??_* \
  # install supercronic
  && curl -fsSL "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64" \
     -o /usr/local/bin/supercronic \
  && echo "${SUPERCRONIC_SHA1SUM}  /usr/local/bin/supercronic" | sha1sum -c - \
  && chmod +x /usr/local/bin/supercronic \
  # Install python dependencies and clean up build dependencies
  && pip install --no-cache-dir -r python-requirements/requirements-all.txt \
  && apt-get -y autoremove

# Copy frontend dist folder to static
WORKDIR /code/src/os2datascanner/projects/static
COPY --from=frontend /code/src/os2datascanner/projects/static/dist ./dist

ENTRYPOINT ["/code/docker/docker-entrypoint.sh"]

# Base image always has a default (see ARG BASE_IMAGE)
ARG BASE_IMAGE=base
# hadolint ignore=DL3006
FROM ${BASE_IMAGE} AS engine

LABEL org.opencontainers.image.title="OS2datascanner - Engine" \
      org.opencontainers.image.vendor="Magenta ApS" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.url="https://os2datascanner.magenta.dk/" \
      org.opencontainers.image.documentation="https://os2datascanner.readthedocs.io/en/latest/" \
      org.opencontainers.image.source="https://github.com/os2datascanner/os2datascanner"

ENV OS2DS_ENGINE_SYSTEM_CONFIG_PATH=/code/docker/docker-settings.toml \
  OS2DS_ENGINE_USER_CONFIG_PATH=/user-settings.toml

RUN groupadd -g 63030 -r os2ds_engine \
  && useradd -u 63030 --no-log-init -r -g os2ds_engine os2ds_engine

COPY docker/engine/docker-settings.toml /code/docker/docker-settings.toml
COPY docker/engine/docker-entrypoint.sh /code/docker/docker-entrypoint.sh

# Copy code
WORKDIR /code/src/os2datascanner
COPY src/os2datascanner/ ./

# Set up to run given command as the new user
USER os2ds_engine:os2ds_engine

EXPOSE 9091
CMD ["explorer", "--help"]

# Base image always has a default (see ARG BASE_IMAGE)
ARG BASE_IMAGE=base
# hadolint ignore=DL3006
FROM ${BASE_IMAGE} AS api

LABEL org.opencontainers.image.title="OS2datascanner - API" \
      org.opencontainers.image.vendor="Magenta ApS" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.url="https://os2datascanner.magenta.dk/" \
      org.opencontainers.image.documentation="https://os2datascanner.readthedocs.io/en/latest/" \
      org.opencontainers.image.source="https://github.com/os2datascanner/os2datascanner"

ENV OS2DS_SERVER_SYSTEM_CONFIG_PATH=/code/docker/docker-settings.toml \
  OS2DS_SERVER_USER_CONFIG_PATH=/user-settings.toml

RUN groupadd -g 63050 -r os2ds_api\
  && useradd -u 63050 --no-log-init -r -g os2ds_api os2ds_api

WORKDIR /code/docker
COPY docker/api/docker-settings.toml ./docker-settings.toml
COPY docker/api/gunicorn-settings.py ./gunicorn-settings.py

# Copy code
WORKDIR /code/src/os2datascanner
COPY src/os2datascanner/ ./

WORKDIR /code/src/os2datascanner/server
USER os2ds_api:os2ds_api
EXPOSE 5000

ENTRYPOINT []
CMD ["gunicorn", \
     "--config", "/code/docker/gunicorn-settings.py", \
     "os2datascanner.server.wsgi"]

# Base image always has a default (see ARG BASE_IMAGE)
ARG BASE_IMAGE=base
# hadolint ignore=DL3006
FROM ${BASE_IMAGE} AS admin

LABEL org.opencontainers.image.title="OS2datascanner - Administration" \
      org.opencontainers.image.vendor="Magenta ApS" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.url="https://os2datascanner.magenta.dk/" \
      org.opencontainers.image.documentation="https://os2datascanner.readthedocs.io/en/latest/" \
      org.opencontainers.image.source="https://github.com/os2datascanner/os2datascanner"

ENV OS2DS_ADMIN_SYSTEM_CONFIG_PATH=/code/docker/docker-settings.toml \
  OS2DS_ADMIN_USER_CONFIG_PATH=/user-settings.toml \
  DJANGO_SETTINGS_MODULE=os2datascanner.projects.admin.settings

RUN groupadd -g 63020 -r os2ds_admin \
  && useradd -u 63020 --no-log-init -r -g os2ds_admin os2ds_admin \
  && install -o os2ds_admin -g os2ds_admin -d /code/uploads/admin \
  && install -o os2ds_admin -g os2ds_admin -d /code/static \
  && install -o os2ds_admin -g os2ds_admin -d /code/build \
  && install -o os2ds_admin -g os2ds_admin -d /code/var

WORKDIR /code/docker/
COPY docker/admin/crontab ./crontab
COPY docker/admin/docker-settings.toml ./docker-settings.toml
COPY docker/insecure-settings.toml ./insecure-settings.toml
COPY docker/docker-entrypoint-django.sh ./docker-entrypoint.sh
COPY docker/gunicorn-settings.py ./gunicorn-settings.py

# Copy code
WORKDIR /code/src/os2datascanner
COPY src/os2datascanner/ ./

# Run the server as the os2ds_admin user on port 5000
WORKDIR /code/src/os2datascanner/projects/admin

# Make os2ds_admin owner of /code/docker. This is only needed to remove the
# insecure settings file after `collectstatic`.
RUN chown -R os2ds_admin:os2ds_admin /code/docker

USER os2ds_admin:os2ds_admin

# Unfortunately, `manage.py` requires all settings to be set. We include a set
# of insecure setting here for only this purpose. We make sure to delete it
# afterward. If `insecure-settings.toml` is found in any production image,
# consider it a bug. See `insecure-settings.toml` for a detailed explanation.
RUN set -ex \
  && OS2DS_ADMIN_USER_CONFIG_PATH=/code/docker/insecure-settings.toml python manage.py collectstatic --no-input --clear \
  && OS2DS_ADMIN_USER_CONFIG_PATH=/code/docker/insecure-settings.toml python manage.py compilemessages \
  && rm /code/docker/insecure-settings.toml

EXPOSE 5000
ENTRYPOINT ["/code/docker/docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "/code/docker/gunicorn-settings.py", "asgi", "os2datascanner.projects.report.asgi:application"]

ARG COMMIT_TAG
ARG COMMIT_SHA
ARG CURRENT_BRANCH
ENV COMMIT_TAG=${COMMIT_TAG} \
    COMMIT_SHA=${COMMIT_SHA} \
    CURRENT_BRANCH=${CURRENT_BRANCH}

# Base image always has a default (see ARG BASE_IMAGE)
ARG BASE_IMAGE=base
# hadolint ignore=DL3006
FROM ${BASE_IMAGE} AS report

LABEL org.opencontainers.image.title="OS2datascanner - Report" \
      org.opencontainers.image.vendor="Magenta ApS" \
      org.opencontainers.image.licenses="MPL-2.0" \
      org.opencontainers.image.url="https://os2datascanner.magenta.dk/" \
      org.opencontainers.image.documentation="https://os2datascanner.readthedocs.io/en/latest/" \
      org.opencontainers.image.source="https://github.com/os2datascanner/os2datascanner"

ENV OS2DS_REPORT_SYSTEM_CONFIG_PATH=/code/docker/docker-settings.toml \
  OS2DS_REPORT_USER_CONFIG_PATH=/user-settings.toml \
  DJANGO_SETTINGS_MODULE=os2datascanner.projects.report.settings

RUN groupadd -g 63040 -r os2ds_report\
  && useradd -u 63040 --no-log-init -r -g os2ds_report os2ds_report \
  && install -o os2ds_report -g os2ds_report -d /code/build \
  && install -o os2ds_report -g os2ds_report -d /code/static \
  && install -o os2ds_report -g os2ds_report -d /code/var

WORKDIR /code/docker/
COPY docker/report/crontab ./crontab
COPY docker/report/docker-settings.toml ./docker-settings.toml
COPY docker/insecure-settings.toml ./insecure-settings.toml
COPY docker/docker-entrypoint-django.sh ./docker-entrypoint.sh
COPY docker/gunicorn-settings.py ./gunicorn-settings.py

# Copy code
WORKDIR /code/src/os2datascanner
COPY src/os2datascanner/ ./

# Run the server as the os2ds_report user on port 5000
WORKDIR /code/src/os2datascanner/projects/report
# Make os2ds_report owner of /code/docker. This is only needed to remove the
# insecure settings file after `collectstatic`.
RUN chown -R os2ds_report:os2ds_report /code/docker

USER os2ds_report:os2ds_report

# Unfortunately, `manage.py` requires all settings to be set. We include a set
# of insecure setting here for only this purpose. We make sure to delete it
# afterward. If `insecure-settings.toml` is found in any production image,
# consider it a bug. See `insecure-settings.toml` for a detailed explanation.
RUN set -ex \
  && OS2DS_REPORT_USER_CONFIG_PATH=/code/docker/insecure-settings.toml python manage.py collectstatic --no-input --clear \
  && OS2DS_REPORT_USER_CONFIG_PATH=/code/docker/insecure-settings.toml python manage.py compilemessages \
  && rm /code/docker/insecure-settings.toml

EXPOSE 5000
ENTRYPOINT ["/code/docker/docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "/code/docker/gunicorn-settings.py", "asgi", "os2datascanner.projects.report.asgi:application"]
