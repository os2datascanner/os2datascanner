Installation
============

**TL;DR:**
To get a development environment to run, follow these steps:

#. Clone the repo and start the containers:
    .. code-block:: bash

        git clone https://github.com/os2datascanner/os2datascanner.git
        cd os2datascanner
        docker-compose up -d

    You can now reach the following services on their respective ports:

    - Administration module: http://localhost:8020
    - Web interface for message queues: http://localhost:8030
    - Report module: http://localhost:8040

    (see `Services`_ for further information)

#. Create logins for the django modules
    Logins for the django modules (Administration and Report) must be created when
    the development environment is first started (and any time the data volume has
    been wiped).
    Having started the environment as described above, simply run

    .. code-block:: bash

        docker-compose exec admin_application python manage.py createsuperuser
        docker-compose exec report_application python manage.py createsuperuser


    You can pass username and email as arguments to the command by adding
    ``--username <your username>`` and/or  ``--email <your email>`` at the
    end of the snippets above, otherwise you will be prompted for them along with a
    password.

    As of `Django 3.0<https://docs.djangoproject.com/en/3.2/ref/django-admin/#django-admin-createsuperuser/>`_, users can be created "script-like" as

    .. code-block:: bash

        docker-compose exec -e DJANGO_SUPERUSER_PASSWORD=test admin_application python manage.py createsuperuser --noinput --username test --email test@test.dk
        docker-compose exec -e DJANGO_SUPERUSER_PASSWORD=test report_application python manage.py createsuperuser --noinput --username test --email test@test.dk

    Credentials for the message queue web interface can be found in here:

    - ``dev-environment/rabbitmq.env``

#. Start a scan:
    #. Log into the administration module with the newly created superuser at
       http://localhost:8020
    #. Go to ``Administration`` and add an ``Organization``.
    #. Return to the main page, go to ``Regler`` (Rules) and add one.
    #. Go to ``Scannerjob`` and add a webscan using the organization and rule
       just created for a website - e.g. ``https://www.magenta.dk``

       **NB!** Please note that OS2datascanner has been built to scan an
       organization's *own* data sources, and to do so as efficiently as
       possible. Thus, OS2datascanner does not check for or adhere to e.g.
       ``robots.txt`` files, and may as a consequence overload a system or
       trigger automated safety measures; **always ensure that the site
       administrator is okay with scanning the site!**
    #. Start the scan by clicking the play button and confirming your choice.

#. Follow the engine activity in RabbitMQ (optional):
    #. Log into the web interface for RabbitMQ - using the credentials
       mentioned above - at
       http://localhost:8030
    #. Queue activity is available on the ``Queues`` tab.

#. See the results:
    #. Log into the report module with the newly created superuser at
       http://localhost:8040
    #. Go to the django admin site at
       http://localhost:8040/admin
    #. Create a new ``Remediator`` pointing to the superuser just created.
    #. Return to the main page and check the results - refresh page for updates.

Docker
------

The repository contains a ``Dockerfile`` for each of the OS2datascanner
modules:

- **Administration**: ``docker/admin/Dockerfile``
- **Engine**: ``docker/engine/Dockerfile``
- **Report**: ``docker/report/Dockerfile``

Using these is the recommended way to
install OS2datascanner as a developer.

.. TODO: adjust section when the set-up has matured.
    `as a developer` -> `both as a developer and in production.

    All releases are pushed to Docker Hub at <link to our registry> under the
    ``latest`` tag.

To run OS2datascanner in Docker, you need a running Docker daemon. See
`the official Docker documentation <https://docs.docker.com/install/>` for
installation instructions.

The containers for the Admin and Report modules require a connection to a
postgres database server. It is configured with the ``DATABASE_*`` settings.
The database server must have a user and a database object. It can be created
with the help of the scripts in the ``/docker/postgres-initdb.d/`` folder:

- ``docker/postgres-initdb.d/20-create-admin-db-and-user.sh``
- ``docker/postgres-initdb.d/40-create-report-db-and-user.sh``

The folder can easily be mounted into ``/docker-entrypoint-initdb.d/`` in
`the official postgres docker image <https://hub.docker.com/_/postgres>`_, and
further contains a script to ensure that all relevant environment variables
have been passed to the container:

- ``docker/postgres-initdb.d/10-test-for-valid-env-variables.sh``

To run a fully functional OS2datascanner system, you will need to start a number
of services. The recommended way to set up an appropriate development environment
is to use `Docker-compose`_.

.. TODO: fill in section on starting each service when the set-up has matured.

..
    Static files
    ^^^^^^^^^^^^

..
    Logs
    ^^^^

User permissions
^^^^^^^^^^^^^^^^

Each ``Dockerfile`` creates a dedicated user, and any services started are run
as the user created by the related ``Dockerfile``. All files generated by such
a service will be owned by the respective user. For each user, the ``UID`` and
``GID`` are identical:

- **Administration**: 73020
- **Engine**: 73030
- **Report**: 73040

If you want to use another ``UID/GID``, you can specify it as the
``--user=uid:gid``
`overwrite flag <https://docs.docker.com/engine/reference/run/#user>`_. for the
``docker run`` command or
`in docker-compose <https://docs.docker.com/compose/compose-file/#domainname-hostname-ipc-mac_address-privileged-read_only-shm_size-stdin_open-tty-user-working_dir>`_.
If you change the ``UID/GID``, the ``/log`` and ``/static`` volumes may not
have the right permissions. It is recommended to only use
`bind <https://docs.docker.com/storage/bind-mounts/>`_ if you overwrite the
user and set the same user as owner of the directory you bind.


Missing permissions in development environment
**********************************************

During development, we mount our local editable files into the docker containers
which means they are owned by the local user, and **not** the user running
inside the container. Thus any processes running inside the container,
like management commands, will not be allowed to create or update files in the
mounted locations.

In order to fix this, we need to allow "others" to write to the relevant
locations. This can be done with ``chmod -R o+w <path>``
(``o`` is for "other users", ``+w`` is to add write-permissions and ``-R`` is
used to add the permissions recursively down through the file structure from
the location ``<path>`` points to).

The above is necessary whenever a process needs write permissions, but should
always be done for the following locations:

* ``code/src/os2datascanner/projects/<module>/locale/``
* ``code/src/os2datascanner/projects/<module>/<module>app/migrations/``

``<module>`` being either ``admin`` or ``report``.

**NB!** Git will only save executable permissions, which means that granting
other users write permissions on your local setup, will not compromise
production security.

..
    Test
    ^^^^

Docker-compose
--------------

You can use ``docker-compose`` to start the OS2datascanner system and its runtime
dependencies (PostgreSQL and RabbitMQ).

A ``docker-compose.yml`` for development is included in the repository. It
specifies the settings to start and connect all required services.

Services
^^^^^^^^

The main services for OS2datascanner are:

- ``admin_frontend``:
    Only needed in development.

    Watches the frontend files and provides support for rebuilding the frontend
    easily during the development process.
- ``admin_application``:
    Reachable on: http://localhost:8020

    Runs the django application that provides the administration interface for
    defining and managing organisations, rules, scans etc.
- ``engine_explorer``:
    Runs the **explorer** stage of the engine.
- ``engine_processor``:
    Runs the **processor** stage of the engine.
- ``engine_matcher``:
    Runs the **matcher** stage of the engine.
- ``engine_tagger``:
    Runs the **tagger** stage of the engine.
- ``engine_exporter``:
    Runs the **exporter** stage of the engine.
- ``report_frontend``:
    Only needed in development.

    Watches the frontend files and provides support for rebuilding the frontend
    easily during the development process.
- ``report_application``:
    Reachable on: http://localhost:8040

    Runs the django application that provides the interface for accessing and
    handling reported matches.
- ``report_collector``:
    Runs the **collector** service that saves match results to the database of
    the report module.

These depend on some auxillary services:

- ``db``:
    Runs a postgres database server based on
    `the official postgres docker image`_.
- ``queue``:
    Runs a RabbitMQ message queue server based on
    `the official RabbitMQ docker image`_, including a plugin providing a web
    interface for monitoring (and managing) queues and users.

    The web interface can be reached on: http://localhost:8030

.. _`the official postgres docker image`: https://hub.docker.com/_/postgres
.. _`the official RabbitMQ docker image`: https://hub.docker.com/_/rabbitmq/

Postgres initialisation
^^^^^^^^^^^^^^^^^^^^^^^

The postgres database is initialized using the scripts included in
``docker/postgres-initdb.d/`` folder, which checks that the configuration is
valid, and adds **postgres users** for the modules that need them.
They do not populate the database with users for the django modules or any
other data.

Gunicorn worker configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The two Django apps and the API use ``Gunicorn`` to serve web requests. By default Gunicorn 
starts up ``CPU_COUNT*2+1`` workers. To override this default use the ``GUNICORN_WORKERS`` 
environment variable. Eg. ``GUNICORN_WORKERS=2``.

Django application users
^^^^^^^^^^^^^^^^^^^^^^^^

As mentioned above, the system is not initialised with any default users for
the django applications. Instead, these will need to be created by running

.. code-block:: bash

    docker-compose {exec|run} {admin|report}-application python manage.py createsuperuser [--username <your username>] [--email <your email>]

where ``exec`` is used when the development environment is already running, and
``run`` when it is not.

If you find yourself having to wipe the database often, you may find it helpful
to write a small script to aid with this, e.g.:

.. code-block:: bash

    # Go to correct directory
    cd <path to repository root>
    # create admin user:
    echo "Creating superuser for admin module..."
    docker-compose <command> admin_application python manage.py createsuperuser --username <your username> --email <your email>
    # create report user:
    echo "Creating superuser for report module..."
    docker-compose <command> report_application python manage.py createsuperuser --username <your username> --email <your email>

**NB!** Make sure your script is **not** added to the repo: add the file (or a
separate folder it lives in) to the global list for git to ignore (usually
``~/.config/git/ignore``, of which you may have to create the ``git`` folder
and the ``ignore`` file yourself).

Tests
=====

Each module has its own test-suite. These are run automatically as part of the
CI pipeline, which also produces a code coverage report for each test-suite.

During development, the test can be run using the relevant Docker image for
each module. As some of the tests are integration tests that require auxiliary
services - such as access to a database and/or message queue - we recommend
using the development docker-compose set-up to run the tests, as this takes care
of the required settings and bindings.

To run the test-suites using docker-compose:

.. code-block:: bash

    docker-compose run admin_application python -m django test os2datascanner.projects.admin.tests
    docker-compose run engine_explorer python -m unittest discover -s /code/src/os2datascanner/engine2/tests
    docker-compose run report_application python -m django test os2datascanner.projects.report.tests

Please note that the engine tests can be run using any of the five pipeline
services as the basis, but a specific one is provided above for easy reference.

.. TODO: Add section on running the test suite when scripts for the
    proper permissions in postgres has been added. Possibly add a script for
    running the tests, compiling the report, and exposing/binding it to the
    host.

Shell access
============

To access a shell on any container based on the OS2datascanner module images,
run

.. code-block:: bash

    docker-compose {exec|run} <container name> bash

Debugging
=========

Stacktrace
^^^^^^^^^^

A stacktrace is printed to `stderr` if pipeline components receive `SIGUSR1`. The
scan continues without interuption.

The components must be startet using `run_stage`

Running the engine locally,
.. code-block:: bash
    python -m os2datascanner.engine2.pipeline.run_stage worker
    ps aux | grep os2datascanner
    kill -USR1 <pid>

Running the engine in Docker, using the namespace sharing between localhost and docker
.. code-block:: bash
    docker top os2datascanner_engine_worker_1  # get the <pid> of the python process
    kill -USR1 <pid>
    docker logs os2datascanner_engine_worker_1


Documentation
=============

The documentation can be found at the `OS2datascanner pages on Read the Docs`_

.. _`OS2datascanner pages on Read the Docs`: https://os2datascanner.readthedocs.io/en/latest

.. TODO: add section on how to build locally and how to access the artifact
    generated by the pipeline, when this has been setup in the new GitLab CI

Code standards
==============

The coding standards below should be followed by all new and edited code for
the project. Linting checks are applied, but currently allowed to fail;
introducing a hard requirement would mean having to fill the version control
history with commits only related to style, which is considered undesirable.

.. TODO: add section on shellcheck and Hadolint, when the new CI pipeline is up

Licensing
=========

The OS2datascanner was programmed by Magenta ApS (https://magenta.dk)
for OS2 - Offentligt digitaliseringsfællesskab, https://os2.eu.

Copyright (c) 2014-2020, OS2 - Offentligt digitaliseringsfællesskab.

The OS2datascanner is free software; you may use, study, modify and
distribute it under the terms of version 2.0 of the Mozilla Public
License. See the LICENSE file for details. If a copy of the MPL was not
distributed with this file, You can obtain one at
http://mozilla.org/MPL/2.0/.

All source code in this and the underlying directories is subject to
the terms of the Mozilla Public License, v. 2.0. 
