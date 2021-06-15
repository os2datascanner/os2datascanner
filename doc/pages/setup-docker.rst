.. include:: ../links.rst

.. _`docker-install`:

Docker-based install
++++++++++++++++++++

For general information on using Docker and ``docker-compose``, please refer to
`the official Docker documentation`__.

__ `docker-doc`_

Docker images and services
==========================

As mentioned in the :ref:`system overview<system-overview>`, the OS2datascanner
consists of three components, or modules. These are each responsible for one
or more services in the system:

* **Admin-module**: The application for the *administration interface*

  - Service: ``admin_application``
  - Service: ``admin_collector``

* **Engine-module**: The services for each of the stages that make up the *scanner engine*:

  - Service: ``engine_explorer``
  - Service: ``engine_processor``
  - Service: ``engine_matcher``
  - Service: ``engine_tagger``
  - Service: ``engine_exporter``

``processor``, ``matcher`` and ``tagger`` can also be started as a single
service, ``engine_worker``.

* **Report-module**: The services concerning the *report interface*

  - Service: ``report_application``
  - Service: ``report_collector``

Furthermore, the system integrates with some auxiliary services (some of which
are optional):

* PostgreSQL (databases)
* RabbitMQ (message queues)
* *Optional:*

  - Prometheus (storage and API for metrics)
  - Grafana (visualisation of metrics)


Installing the system
=====================

The Docker images
-----------------

All images related to OS2datascanner can be found
`on Magenta's Docker image repository`__, but here follows the images names for
the three modules, with links to the module repositories:

* **Admin-module**:
    - `magentaaps/os2datascanner-admin`__
* **Engine-module**:
    - `magentaaps/os2datascanner-engine`__
* **Report-module**:
    - `magentaaps/os2datascanner-report`__

Furthermore, we have made an adapted postgres image with dedicated users for
the OS2datascanner system (to avoid giving root privileges to the OS2datascanner
users in the postgres container):

* **Adapted postgres image**:
    - `magentaaps/os2datascanner-db`__

__ `docker-images-magenta`_
__ `docker-images-os2ds-admin`_
__ `docker-images-os2ds-engine`_
__ `docker-images-os2ds-report`_
__ `docker-images-os2ds-db`_

This last image is made available for anyone who wishes to run their
OS2datascaner databases in a Docker container, rather than directly on the host.
The image allows for the two databases (one for the Admin-module, one for the
Report-module) to be run from a single container or from a container each. It
is configured through seven environment variables - the superuser and at least
one set of three module-related variable are required:

.. literalinclude:: ../samples/db.env
  :language: ini


System configuration
--------------------

All three modules are configured using a `.toml`-file (one for each module) as
described in :ref:`the section on configuration<system-configuration>`.
When installing
using Docker, these files need to be mounted correctly as described below.

Running the system
------------------

OS2datascanner is a multi-service system, and as such also a multi-container
system. It may be advantageous to run it using ``docker-compose``, and we end
this section with `an example of a docker-compose set-up`__.

__ `docker-compose-sample`_

Each service for the OS2datascanner system can be started using the `docker`
command. Note that some configurations can be adapted
to the individual host - we give the options required to parallel the setup in
the following ``docker-compose.yml`` file for easier reference in the rest of
the documentation.

* **Service**: ``admin_application``

  Command:

  :code:`docker run -d -p 8020:5000 --mount type=bind,source="$(pwd)"/admin-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-admin`

* Service: ``engine_explorer``

  Command:

  :code:`docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine explorer`

* Service: ``engine_processor``

  Command:

  :code:`docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine processor`

* Service: ``engine_matcher``

  Command:

  :code:`docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine matcher`

* Service: ``engine_tagger``

  Command:

  :code:`docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine tagger`

* Service: ``engine_exporter``

  Command:

  :code:`docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine exporter`

* Service: ``report_application``

  Command:

  :code:`docker run -d -p 8040:5000 --mount type=bind,source="$(pwd)"/report-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-report`

* Service: ``report_collector``

  Command:

  :code:`docker run -d --mount type=bind,source="$(pwd)"/report-user-settings.toml,target=/user-settings.toml,readonly -e OS2DS_SKIP_DJANGO_MIGRATIONS=1 magentaaps/os2datascanner-report python manage.py pipeline_collector`


Furthermore, OS2datascanner depends PostgreSQL for the two databases (one each
for the Admin- and Report modules), and a RabbitMQ service. Both can
be run directly on the host, or using docker images. Note that the
:ref:`configuration of OS2datascanner<system-configuration>` should match whichever
set-up is chosen for the databases and message queue.


.. _`docker-compose-sample`:

docker-compose set-up for development
-------------------------------------

The ``docker-compose.yml`` use ``--profiles`` which requires version
``docker-compose > 1.28``.

To start the core components(``engine``, ``report``- and ``admin`` interface,
``db`` and ``queue``) of datascanner, use

.. code-block:: sh

   docker-compose up -d

To start a service behind a ``profiles`` flag, use

.. code-block:: sh

   docker-compose --profile api up -d

The following ``profiles`` are available: ``ldap``, ``sso``, ``api`` and ``metric``.

See docker-compose.yml_ for more. The development config files are stored in
``os2datascanner/dev-environment/``

.. _docker-compose.yml: https://github.com/os2datascanner/os2datascanner/blob/master/docker-compose.yml
