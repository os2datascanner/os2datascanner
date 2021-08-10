# "Raw" install


## Installing the system

Installing OS2Datascanner as a whole requires root-level access, and the
installation process will configure and manipulate operating system-level
services. As such, development environments should normally be installed in an
appropriate virtual machine.

Note that some parts of OS2Datascanner *are* suitable for use in a normal
Python environment:

-   the `os2datascanner.engine2.rules` module, which defines search rules,
    logical operators, and content conversions; and
-   the `os2datascanner.engine2.model` module and its submodules, which define
    sources of scannable things and exploration strategies.

This is partly a principled decision to keep the scanner engine loosely
coupled to the rest of the system, and partly a practical move to make
development easier, as most new development takes place in these
packages.


## Preparing the Development environment

From the installation folder, run the
`contrib/system-scripts/development/development_setup.sh` script as root; this
will install all of the necessary system dependencies, set up a Python virtual
environment in the `python-env/` folder and perform django migrations for both
the *administration interface* and the *report interface*. You will be asked to
enter a password for the default superadmin user named os2, for both
interfaces.


### Preparing the Production environment

From the installation folder, run the
`contrib/system-scripts/production/production_deploy.sh` script as root;
This will install and setup all the necessary components. Before the
installation can begin you will have to provide the
`contrib/system-scripts/production/production_deploy.sh` script with the
path to the production directory and with domain names to the two
*interfaces*. The *report interface* should always have the postfix
*-report* to the domain name.

After the installation you will have to provide the system with valid
ssl certificates. The installation expects the certificates to be
located in the folder `/etc/apache2/certs/datascanner`. Edit the two
apache2 configuration files which can be found
`contrib/config/admin-module/admin-vhost.conf` and
`contrib/config/report-module/report-vhost.conf`.

If the *report interface* shall have SAML2 authentication enabled you
will have to provide the
`contrib/config/report-module/local_settings.py` file with the necessary
information manually.

For how to start the different services go to
`systemd`{.interpreted-text role="ref"}

### Preparing Prometheus (optional)

OS2Datascanner\'s pipeline stages use Prometheus to provide live status
monitoring. To configure a local Prometheus server to collect data from
the pipeline components, run the `setup/prometheus_setup.sh` script as
root.

## Starting the system

For debugging, it\'s often easiest to start all of the OS2Datascanner
components in a terminal. The `bin/` folder contains a number of
convenience scripts for doing this:

-   `bin/pex` runs its command-line arguments in the context of the
    Python virtual environment and with a working directory of `src/`.
    (The rest of the scripts are built around this command.)
-   `bin/manage-admin` runs the Django `manage.py` script for the
    administration interface.
-   `bin/manage-report` runs the Django `manage.py` script for the
    report interface.

### Starting development Django web servers

Django\'s `manage.py` script has a `runserver` subcommand for running
development web servers. Run `bin/manage-admin runserver 0:8000` to
start the administration interface on port 8000, and
`bin/manage-report runserver 0:8001` to start the report interface on
port 8001.

### Starting the pipeline

The pipeline\'s stages can either be run in a foreground terminal, which
is useful for debugging and development, or through `systemd`. (Mixed
approaches are also possible: for example, `systemd` can be used to
manage most of the stages while one or two are run in a terminal with
special debugging options.)

#### In a terminal

The five stages of the pipeline are normal Python programs, implemented
by five modules in the `src/os2datascanner/engine2/pipeline/` directory.
Start them with the following commands:

> -   `bin/pex python -m os2datascanner.engine2.pipeline.explorer`
> -   `bin/pex python -m os2datascanner.engine2.pipeline.processor`
> -   `bin/pex python -m os2datascanner.engine2.pipeline.matcher`
> -   `bin/pex python -m os2datascanner.engine2.pipeline.tagger`
> -   `bin/pex python -m os2datascanner.engine2.pipeline.exporter`

Note that these commands will remain in the foreground to print status
information.

#### With `systemd` {#systemd}

The `contrib/systemd/` folder contains `systemd` unit templates for the
pipeline stages. These templates also include some isolation settings
which run the pipeline stages as unprivileged users and prevent them
from modifying the local filesystem.

Start the stages with the following command:

> `systemctl start os2ds-explorer@0.service os2ds-processor@0.service os2ds-matcher@0.service os2ds-tagger@0.service os2ds-exporter@0.service`

It\'s also possible to use these unit templates to start multiple
instances of, for example, the processor stage:

> `systemctl start os2ds-processor@1.service os2ds-processor@2.service os2ds-processor@3.service`

`systemd` subcommands also support wildcards, which can be used to get
an overview of the entire pipeline at once:

> `systemctl status os2ds-*.service`

### Starting the collector

The report module has a separate component, the *pipeline collector*,
that reads results from the pipeline and inserts them into its database.
This is exposed as a Django management command through the
`bin/manage-report` script:

> `bin/manage-report pipeline_collector`

Run this command (which, again, will remain in the foreground) to make
pipeline results available to the report interface.


# Docker-based install

For general information on using Docker and `docker-compose`, please refer to
[the official Docker documentation](https://docs.docker.com/).


## Docker images and services

As mentioned in the [system overview](./index.md), the OS2Datascanner consists
of three components, or modules. These are each responsible for one or more
services in the system:

-   **Admin-module**: The application for the *administration interface*
    -   Service: `admin`
    -   Service: `admin_collector`
-   **Engine-module**: The services for each of the stages that make up
    the *scanner engine*:
    -   Service: `explorer`
    -   Service: `processor`
    -   Service: `matcher`
    -   Service: `tagger`
    -   Service: `exporter`

`processor`, `matcher` and `tagger` can also be started as a single service,
`worker`. This is the default (and recommended) configuration, as its
cache use is much more efficient.

-   **Report-module**: The services concerning the *report interface*
    -   Service: `report`
    -   Service: `report_collector`

Furthermore, the system integrates with some auxiliary services (some of
which are optional):

-   PostgreSQL (databases)
-   RabbitMQ (message queues)
-   *Optional:*
    -   Prometheus (storage and API for metrics)
    -   Grafana (visualisation of metrics)


## Installing the system


### The Docker images

All images related to OS2datascanner can be found [on Magenta's Docker image
repository](https://hub.docker.com/u/magentaaps), but here follows the images
names for the three modules, with links to the module repositories:

- **Admin-module**: [magentaaps/os2datascanner-admin](https://hub.docker.com/r/magentaaps/os2datascanner-admin)
- **Engine-module**: [magentaaps/os2datascanner-engine](https://hub.docker.com/r/magentaaps/os2datascanner-engine)
- **Report-module**: [magentaaps/os2datascanner-report](https://hub.docker.com/r/magentaaps/os2datascanner-report)

Furthermore, we have made an adapted postgres image with dedicated users for
the OS2datascanner system (to avoid giving root privileges to the
OS2datascanner users in the postgres container):

- **Adapted postgres image**: [magentaaps/os2datascanner-db](https://hub.docker.com/r/magentaaps/os2datascanner-db)

This last image is made available for anyone who wishes to run their
OS2datascaner databases in a Docker container, rather than directly on the
host. The image allows for the two databases (one for the Admin-module, one for
the Report-module) to be run from a single container or from a container each.
It is configured through seven environment variables - the superuser and at
least one set of three module-related variable are required:

```bash
# SUPERUSER password
POSTGRES_PASSWORD=<super user password for postgres instance>

# Admin user
ADMIN_DATABASE_NAME=os2datascanner_admin
ADMIN_DATABASE_USER=<user name for admin module db user>
ADMIN_DATABASE_PASSWORD=<password for admin module db user>

# Report user
REPORT_DATABASE_NAME=os2datascanner_report
REPORT_DATABASE_USER=<user name for report module db user>
REPORT_DATABASE_PASSWORD=<password for report module db user>
```


### System configuration

All three modules are configured using a TOML-file (one for each module) as
described in [the section on configuration](configuration.md). When installing
using Docker, these files need to be mounted correctly as described below.


### Running the system

OS2datascanner is a multi-service system, and as such also a multi-container
system. It may be advantageous to run it using `docker-compose`. A
[docker-compose file for
development](https://github.com/os2datascanner/os2datascanner/blob/master/docker-compose.yml)
is in the repository root.

Each service for the OS2datascanner system can be started using docker.  Note
that some configurations can be adapted to the individual host - we give the
options required to parallel the setup in the following `docker-compose.yml`
file for easier reference in the rest of the documentation.

| Service          | Command                                                                                                                                                                                                                    |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| admin            | `docker run -d -p 8020:5000 --mount type=bind,source="$(pwd)"/admin-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-admin`                                                                |
| report           | `docker run -d -p 8040:5000 --mount type=bind,source="$(pwd)"/report-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-report`                                                              |
| report_collector | `docker run -d --mount type=bind,source="$(pwd)"/report-user-settings.toml,target=/user-settings.toml,readonly -e OS2DS_SKIP_DJANGO_MIGRATIONS=1 magentaaps/os2datascanner-report python manage.py pipeline_collector`     |
| explorer         | `docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine explorer`                                                                  |
| processor        | `docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine processor`                                                                 |
| matcher          | `docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine matcher`                                                                   |
| tagger           | `docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine tagger`                                                                    |
| exporter         | `docker run -d --mount type=bind,source="$(pwd)"/engine-user-settings.toml,target=/user-settings.toml,readonly magentaaps/os2datascanner-engine exporter`                                                                  |

    

Furthermore, OS2datascanner depends PostgreSQL for the two databases (one each
for the Admin- and Report modules), and a RabbitMQ service.  Both can be run
directly on the host, or using docker images. Note that the [configuration of
OS2datascanner](configuration.md) should match whichever set-up is chosen for
the databases and message queue.


### docker-compose set-up for development

The `docker-compose.yml` use `--profiles` which requires version
`docker-compose > 1.28`.

To start the core components(`engine`, `report`- and `admin` interface, `db`
and `queue`) of datascanner, use

```sh
docker-compose up -d
```

To start a service behind a `profiles` flag, use

```sh
docker-compose --profile api up -d
```

The following `profiles` are available: `ldap`, `sso`, `api` and `metric`.

The development config files are stored in `os2datascanner/dev-environment/`
