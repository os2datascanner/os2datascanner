.. _`raw-install`:

"Raw" install
+++++++++++++

Installing the system
=====================

Installing OS2datascanner as a whole requires root-level access, and the
installation process will configure and manipulate operating system-level
services. As such, development environments should normally be installed in an
appropriate virtual machine.

(Note that some parts of OS2datascanner *are* suitable for use in a normal
Python environment:

* the ``os2datascanner.engine2.rules`` module, which defines search rules,
  logical operators, and content conversions; and
* the ``os2datascanner.engine2.model`` module and its submodules, which define
  sources of scannable things and exploration strategies.

This is partly a principled decision to keep the scanner engine loosely coupled
to the rest of the system, and partly a practical move to make development
easier, as most new development takes place in these packages.)

Preparing the Development environment
-------------------------------------

From the installation folder, run the
``contrib/system-scripts/development/development_setup.sh`` script as root;
this will install all of the necessary system dependencies, set up a Python virtual
environment in the ``python-env/`` folder and perform django migrations for
both the *administration interface* and the *report interface*.
You will be asked to enter a password for the default superadmin user named os2,
for both interfaces.

Preparing the Production environment
------------------------------------

From the installation folder, run the
``contrib/system-scripts/production/production_deploy.sh`` script as root;
This will install and setup all the necessary components.
Before the installation can begin you will have to provide the
``contrib/system-scripts/production/production_deploy.sh`` script with the
path to the production directory and with domain names to the two *interfaces*.
The *report interface* should always have the postfix *-report* to the domain name.

After the installation you will have to provide the system with valid ssl certificates.
The installation expects the certificates to be located in the folder
``/etc/apache2/certs/datascanner``.
Edit the two apache2 configuration files which can be found
``contrib/config/admin-module/admin-vhost.conf`` and
``contrib/config/report-module/report-vhost.conf``.

If the *report interface* shall have SAML2 authentication enabled you will have to
provide the ``contrib/config/report-module/local_settings.py`` file with the
necessary information manually.

For how to start the different services go to :ref:`With ``systemd```

Preparing Prometheus (optional)
-------------------------------

OS2datascanner's pipeline stages use Prometheus to provide live status
monitoring. To configure a local Prometheus server to collect data from the
pipeline components, run the ``setup/prometheus_setup.sh`` script as root.

Starting the system
===================

For debugging, it's often easiest to start all of the OS2datascanner components
in a terminal. The ``bin/`` folder contains a number of convenience scripts for
doing this:

- ``bin/pex`` runs its command-line arguments in the context of the Python
  virtual environment and with a working directory of ``src/``. (The rest of
  the scripts are built around this command.)
- ``bin/manage-admin`` runs the Django ``manage.py`` script for the
  administration interface.
- ``bin/manage-report`` runs the Django ``manage.py`` script for the report
  interface.

Starting development Django web servers
---------------------------------------

Django's ``manage.py`` script has a ``runserver`` subcommand for running
development web servers. Run ``bin/manage-admin runserver 0:8000`` to start the
administration interface on port 8000, and ``bin/manage-report runserver
0:8001`` to start the report interface on port 8001.

Starting the pipeline
---------------------

The pipeline's stages can either be run in a foreground terminal, which is
useful for debugging and development, or through ``systemd``. (Mixed approaches
are also possible: for example, ``systemd`` can be used to manage most of the
stages while one or two are run in a terminal with special debugging options.)

In a terminal
^^^^^^^^^^^^^

The five stages of the pipeline are normal Python programs, implemented by five
modules in the ``src/os2datascanner/engine2/pipeline/`` directory. Start them
with the following commands:

  - ``bin/pex python -m os2datascanner.engine2.pipeline.explorer``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.processor``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.matcher``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.tagger``
  - ``bin/pex python -m os2datascanner.engine2.pipeline.exporter``

Note that these commands will remain in the foreground to print status
information.

With ``systemd``
^^^^^^^^^^^^^^^^

The ``contrib/systemd/`` folder contains ``systemd`` unit templates for the
pipeline stages. These templates also include some isolation settings which run
the pipeline stages as unprivileged users and prevent them from modifying the
local filesystem.

Start the stages with the following command:

  ``systemctl start os2ds-explorer@0.service os2ds-processor@0.service
  os2ds-matcher@0.service os2ds-tagger@0.service os2ds-exporter@0.service``

It's also possible to use these unit templates to start multiple instances of,
for example, the processor stage:

  ``systemctl start os2ds-processor@1.service os2ds-processor@2.service
  os2ds-processor@3.service``

``systemd`` subcommands also support wildcards, which can be used to get an
overview of the entire pipeline at once:

  ``systemctl status os2ds-*.service``

Starting the collector
----------------------

The report module has a separate component, the *pipeline collector*, that
reads results from the pipeline and inserts them into its database. This is
exposed as a Django management command through the ``bin/manage-report``
script:

  ``bin/manage-report pipeline_collector``

Run this command (which, again, will remain in the foreground) to make pipeline
results available to the report interface.
