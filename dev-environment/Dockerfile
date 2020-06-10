FROM python:3.6
WORKDIR requirements/sys-requirements
COPY requirements/sys-requirements .
# Combine all system dependencies
RUN cat sys-requirements-*.txt > sys-requirements.txt
RUN cat sys-requirements.txt
RUN set -ex \
# Install system dependencies from file.
  && apt-get -y update \
  && apt-get -y install --no-install-recommends $(grep -o '^[^#][[:alnum:].-]*' sys-requirements.txt)
WORKDIR /requirements/python-requirements
RUN pip install pip-tools
COPY requirements/python-requirements .
# ADD COMMAND FOR COMPILING ALL requirement-*.txt FILES!
