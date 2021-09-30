# Management Commands

OS2Datascanner consists of multiple Django apps, and
each Django app can register their own actions with manage.py.

In our project, we have multiple such actions/commands registered.
 
Custom commands must be created in the correct path (`<app>/management/commands`) of the Django app they concern.

More information regarding how to create custom commands, can be found in [Django's documentation (3.2)](https://docs.djangoproject.com/en/3.2/howto/custom-management-commands/)

## Quick guide to command execution
In general, to execute these commands, do one of the following, dependent on whether your container is already running:

Container running:
`docker-compose exec <app> python manage.py <command>`

Container not running:
`docker-compose run <app> python manage.py <command>`


## Available commands in the project

This section is to be updated continuously when new management commands are implemented.

Command documentation should be placed under the headline they concern,
and what is to be included upon a new command is a short description of it. 

### Admin application

###### list_scannerjobs

This command lists all scanner jobs and the following attributes:   

* Primary Key
* Name
* Start time
* Number of objects scanned
* Scan status (as a bool)
* Checkup messages (as count())

To execute this command run:
`docker-compose exec admin python manage.py list_scannerjobs`


###### quickstart_dev

This command is only intended for getting a developer environment
up-and-running quickly. It creates a user named `dev` with the password `dev`
and registers the Samba share from the `docker-compose` dev env as a filescan.

There is a corresponding command in the Report module.


### Core

### Import services

### Report application

###### scannerjob_info

Provided a PK of a scanner job finds associated document reports and lists:

* Scanner job name & PK
* Total message count
* Problem message count
* Match message count
* Mimetype info and count on messages

To execute this command run:
`docker-compose exec report python manage.py scannerjob_info <PK>`

###### quickstart_dev

This command is only intended for getting a developer environment
up-and-running quickly. It creates a user named `dev` with the password `dev`
and registers the user as remediator.

There is a corresponding command in the Admin module.

###### list_problems

List the problem messages for a scanner job.

Optionally takes a `--head` argument to limit the output.

To execute this command run:
`docker-compose exec report django-admin list_problems <PK>`

###### makefake

Randomizes and creates new data types to populate document reports.

To execute this command run:
`docker-compose exec report python manage.py makefake`
args: 
--scan-count = amount of scans (default: random amount between 5 and 10)
--page-count = amount of pages where at least 1 match will be found (default: random amount between 5 and 10)