# Installation

OS2datascanner is composed of many services. Each service is packaged in Docker
and can be run with any container orchestration system, such as
`docker-compose`. For general information on using Docker and `docker-compose`,
please refer to [the official Docker documentation](https://docs.docker.com/).


## Docker services overview

As mentioned in the [system overview](./index.md), the OS2datascanner consists
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

Furthermore, the system integrates with some backing services (some of
which are optional):

-   PostgreSQL (databases)
-   RabbitMQ (message queues)
-   *Optional:*
    -   Prometheus (storage and API for metrics)
    -   Grafana (visualisation of metrics)


## Docker images

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


## System configuration

All three modules are configured using a TOML-file (one for each module) as
described in [the section on configuration](configuration.md). When installing
using Docker, these files need to be mounted correctly as described below.


## Running the system

OS2datascanner is a multi-service system, and as such also a multi-container
system. It may be advantageous to run it using `docker-compose`. A
[docker-compose file for
development](https://github.com/os2datascanner/os2datascanner/blob/main/docker-compose.yml)
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
