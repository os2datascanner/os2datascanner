FROM python:3.9.7

WORKDIR /requirements/sys-requirements
COPY requirements/sys-requirements .
# Combine all system dependencies
# hadolint ignore=DL3059
RUN cat sys-requirements-*.txt > sys-requirements.txt
# hadolint ignore=DL3059
RUN cat sys-requirements.txt
# hadolint ignore=SC2046,DL3008
RUN set -ex \
# Install system dependencies from file.
  && apt-get -y update \
  && apt-get -y install --no-install-recommends $(grep -o '^[^#][[:alnum:].-]*' sys-requirements.txt) \
  # clean up after apt-get and man-pages
  && apt-get clean && rm -rf "/var/lib/apt/lists/*" "/tmp/*" "/var/tmp/*" "/usr/share/man/??" "/usr/share/man/??_*"

WORKDIR /requirements/python-requirements
RUN pip install --no-cache-dir pip-tools==5.5.0
COPY requirements/python-requirements .

# ADD COMMAND FOR COMPILING ALL requirement-*.txt FILES!
