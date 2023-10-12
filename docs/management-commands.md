# Management Commands

OS2datascanner consists of multiple Django apps, and each Django app can
register their own actions with manage.py.

In our project, we have multiple such actions/commands registered.
 
Custom commands must be created in the correct path
(`<app>/management/commands`) of the Django app they concern.

More information regarding how to create custom commands, can be found in
[Django's documentation
(3.2)](https://docs.djangoproject.com/en/3.2/howto/custom-management-commands/)


## Quick guide to command execution

In general, to execute these commands, do one of the following, dependent on
whether your container is already running:

Container running: `docker-compose exec <app> django-admin <command>`

Container not running: `docker-compose run <app> django-admin <command>`


## Admin application

### `list_scannerjobs`

This command lists all scanner jobs and the following attributes:   

* Primary Key
* Name
* Start time
* Number of objects scanned
* Scan status (as a bool)
* Checkup messages (as count())

To execute this command run:
`docker-compose exec admin python manage.py list_scannerjobs`


### `quickstart_dev`

This command is only intended for getting a developer environment
up-and-running quickly. It creates a user named `dev` with the password `dev`
and registers the Samba share from the `docker-compose` dev env as a filescan.

There is a corresponding command in the Report module.


### `pipelinectl`

This command is used to interact with a running pipeline by sending it a
prioritised "command message" that pipeline components can react to.

Currently, the command can be used to abort running scans, to change the log
log level of the live system, and to obtain profiling information from live
processes.


### `cleanup_account_results`

This command is used to delete all document reports of a specified account
and scanner job. The command is primarily intended for programmatic use, but
can be called manually.

The command must include the following options:

* `--accounts` followed by space-separated UUIDs or usernames of existing 
  accounts.

* `--scanners` followed by space-separated primary keys of existing scanners.

### `diagnostics`

This command is used to give basic information about some objects in the
database. The tool will warn you about certain broken objects or known issues,
such as Account objects with an empty string as a username. The intended use
is an initial automatic analysis of the database, which hopefully leads to
some useful information for further debugging.

The command can be called with the `--only` option, followed by one or more
of the following arguments:

* "Account"
* "Alias"
* "OrganizationalUnit"
* "Organization"
* "UserErrorLog"
* "Rule"

#### Abort a scan

To abort a scan, use **one** of the following flags:

| Flag               | Help                                                                      |
|--------------------|---------------------------------------------------------------------------|
| --abort-scantag    | the tag of a running scan that should be stopped                          |
| --abort-scannerjob | the primary key of a scanner job whose most recent scan should be stopped |
| --abort-scanstatus | the primary key of a ScanStatus object whose scan should be stopped       |

#### Change the log level

To change the log level of the running pipeline, use `--log-level=LEVEL` where
`LEVEL` can be any of `critical`, `error`, `warn`, `warning`, `info` or
`debug`.

#### Switch profiling on and off

To enable runtime profiling for pipeline components, use the `--profile`
parameter. To switch it off again, use `--no-profile`.

While runtime profiling is enabled, Python's `cProfile` profiler will record
details of what each pipeline process is doing and how long it takes.
Disabling runtime profiling will print the active profile to the log
(sorted by the total time spent in each function call) before clearing it and
switching the profiler off.

Attempting to enable runtime profiling while it's already enabled (that is,
calling `pipelinectl --profile` twice) will print and clear the active profile,
effectively resetting the profiler without switching it off.


## Report application


### `scannerjob_info`

Provided a PK of a scanner job finds associated document reports and lists:

* Scanner job name & PK
* Total message count
* Problem message count
* Match message count
* Mimetype info and count on messages

To execute this command run:
`docker-compose exec report python manage.py scannerjob_info <PK>`


### `quickstart_dev`

This command is only intended for getting a developer environment
up-and-running quickly. It creates a user named `dev` with the password `dev`
and registers the user as remediator.

There is a corresponding command in the Admin module.


### `list_problems`

List the problem messages for a scanner job.

Optionally takes a `--head` argument to limit the output.

To execute this command run:
`docker-compose exec report django-admin list_problems <PK>`


### `makefake`

Randomizes and creates new data types to populate document reports.

To execute this command run:
`docker-compose exec report python manage.py makefake`
args: 
--scan-count = amount of scans (default: random amount between 5 and 10)
--page-count = amount of pages where at least 1 match will be found (default: random amount between 5 and 10)

### `performance_scan`

creates and runs 2 (limited by gitlabs runners max timeout) scans and then measures
the average time a scan takes. Also generates a report with cProfile that informs
about which methods have used how much time. However the report only monitors the
admin module when run. In the future the reports generated in the pipeline should 
contain information about the engine components.
the location of the output is a .prof file located in `/src/datascanner/` of the project dir. 
The .prof file is used with snakeviz( pip install snakeviz), to give
an icicle visualization of the performance of the scan.
To see the visualization: `snakeviz {report_location}/performance.prof`

To execute this command run:
`docker-compose exec -u 0 admin python manage.py performance_measurement`

### `diagnostics`

This command is used to give basic information about some objects in the
database. The tool will warn you about certain broken objects or known issues,
such as Account objects with an empty string as a username. The intended use
is an initial automatic analysis of the database, which hopefully leads to
some useful information for further debugging.

The command can be called with the `--only` option, followed by one or more
of the following arguments:

* "Account"
* "Alias"
* "OrganizationalUnit"
* "Organization"
* "DocumentReport"
* "Problem"