***************************
The OS2datascanner scan API
***************************

This document is a short guide to making use of OS2datascanner services from
external systems.

The scan server
===============

The ``os2datascanner.server`` package implements a WSGI-based web server that
lets external systems run OS2datascanner scans. The results that it returns are
equivalent to those sent to the report module by a normal pipeline scan.

    Implementation note: the API server presently *simulates* the pipeline
    internally in order to produce results, but this is not guaranteed to
    remain the case. In future the server might simply become a middleman,
    passing scan specifications to a real pipeline instance and forwarding the
    results.

The messages expected by the API server are documented using the OpenAPI
specification language. This includes a subset of OS2datascanner's ``Rule``\s
(including the logical rules) and ``Source``\s.

    The API server supports *all* of OS2datascanner's ``Rule``s and
    ``Source``\s, not just those present in the OpenAPI documentation.
    
    You can restrict the ``Source``\s to a list of approved types in its
    settings.

The Docker development environment starts the API server on port 8070 along
with a Swagger UI server on port 8075. The latter can be used to experiment
with the API and to view its documentation.

For safety reasons, the API server requires that scan requests carry a bearer
token. Until a value for this token has been specified in the server's
settings, all scan requests will be rejected.

Uploading files to scan
-----------------------

To upload a file to the API server, package it in a ``"data"`` ``Source``. This
is a Base64-encoded representation of the file, accompanied by its media type.
(See the OpenAPI specification file, served by the API server as
``/openapi.yaml``, for more information.)

You can scan multiple files at once by first archiving them in a Zip file or
tarball; OS2datascanner recognises these as explorable containers and will scan
the files that they contain.

The administration system API
=============================

The OS2datascanner administration system also has an API, available at the
``/api/`` path. This API grants limited access to the scanners and rules that
have been defined in the administration system.

    For safety, the ``Source``\s produced by the administration system API are
    *censored* -- they do not contain privileged information such as API keys
    and service account passwords.

Using the administration system API requires that an *API key* UUID be passed
as a bearer token. API key objects must presently be created through the Django
administration interface, and give access only to the objects associated with a
specific ``Organization``.

See the OpenAPI specification file, served by the administration system as
``/api/openapi.yaml``, for more information.
