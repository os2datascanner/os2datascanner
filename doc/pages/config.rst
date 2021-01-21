.. :index:

.. _`system-configuration`:

Configuring OS2datascanner
++++++++++++++++++++++++++

The OS2datascanner system is configured using ``.toml``-files - one for each
module.
Most configuration settings come with reasonable defaults and need not
be changed for a standard set-up, but most can be adjusted as needed,
and a few must be given in order for the system to work.
Below follows minimal examples for each module.

.. TODO: we should add lists of all (user relevant) settings and their purpose
   possibly including sample values

Configuration for the Admin-module
==================================

An almost minimal example of the ``admin-user-settings.toml`` configuration file
can be seen here:

.. literalinclude:: ../samples/admin-user-settings.toml
  :language: TOML


Configuration for the Engine-module
===================================

A minimal example of the ``enginge-user-settings.toml`` configuration file can
be seen here:

.. literalinclude:: ../samples/engine-user-settings.toml
  :language: TOML


Configuration for the Report-module
===================================

An almost minimal example of the ``report-user-settings.toml`` configuration
file can be seen below.
**Please note:** the metadata settings for ``SAML2_AUTH`` are mutually
exclusive, and you should only ever set one of them.

.. literalinclude:: ../samples/report-user-settings.toml
   :language: TOML

