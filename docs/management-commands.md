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