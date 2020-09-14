This folder contains files strictly related to the development environment. 
The development environment is based on Docker images, and is orchestrated using
docker-compose.
The files in this folder are used by ``../docker-compose.yml`` to run the
development environment.

For files related to running the Docker images, see ``../docker/``.

Requirements
------------
To generate requirements in the development environment, a ``Dockerfile`` and a
``docker-compose.yml`` have been provided. The generated Docker image contains
all system dependencies, thus ensuring that ``pip-tools`` pin packages to the
correct versions. To generate the
``../requirements/python-requirements/requirements-*.txt``-files, simply run
::

$ docker-compose up

from the current folder.