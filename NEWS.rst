OS2datascanner
==============

Version 3.3.1, 14th May 2020
----------------------------

"You've Got Mail"

Neither the user interface of version 3 of OS2datascanner nor its underlying
scanner engine would have become as advanced as they are without the efforts of
Steffen Jørgensen and of Dan V. P. Christiansen. The OS2datascanner development
team thanks them for their many contributions.

New in this version:

- Support for handling matches:

  - The report module now has a button for setting the resolution status of a
    match.

  - Resolved matches are hidden from the user interface, but are preserved in
    the database for later reference.

- Support for email notifications:

  - The report module now has a command that sends email notifications of
    unhandled matches to all users.

General improvements:

- All of the unused code in the administration system that was once responsible
  for interacting with the old scanner engine has been removed.

- The appearance of the administration system's user interface elements is now
  changed when they receive focus.

- Many modal dialog boxes have been removed from the administration system,
  giving a more contemporary feel.

Bugfixes:

- The components of the scanner engine's pipeline no longer opportunistically
  prefetch messages, improving error resilience and scalability.

- Scanning Exchange Web Services accounts should no longer produce occasional
  character decoding errors.

- Errors in the metadata extraction process no longer cause all of the relevant
  file's metadata to be discarded.

- Errors in external tools are now handled uniformly.

- Encrypted files in Zip archives are now ignored instead of being
  unsuccessfully processed.

Version 3.3.0, 24rd April 2020
------------------------------

"No Missing Screws"

New in this version:

- Support for scanning websites:

  - Results from website scans are displayed properly in the report module.

  - Report module users can be given responsibility for matches from individual
    web domains.

  - The scanner engine understands and follows links from sitemap and sitemap
    index files.

- The report module's overview now includes a key that lists the various
  sensitivity levels.

General improvements:

- The alignment of the user interface has been improved throughout the
  administration system.

Bugfixes:

- The installation process now correctly builds CSS and JavaScript resources.

- Files uploaded to the administration system are preserved when upgrading
  production installations.

- The Apache configuration files built by the installation process no longer
  contain erroneous paths to installed files.

- Drive letters associated with network drives are now correctly sent from the
  administration system to the scanner engine.

- The administration system now correctly displays sensitivity values for CPR
  rules.

- Attempting to delete a scanner job in the administration system no longer
  produces a broken modal dialog.

- The report module no longer displays an unnecessary vertical scrollbar.

Version 3.2.1, 3rd April 2020
-----------------------------

"Direct Hit"

New in this version:

- The report module now provides a direct link to matches in Office 365 email
  messages.

General improvements:

- The installation process now supports more kinds of deployment.

- The scanner engine is now more resilient against internal communication
  problems.

- The process of extracting plain text from documents with structure or
  formatting now produces more natural results.

- Individual matches can now also carry sensitivity values for higher
  precision.

Bugfixes:

- Scanner jobs with no associated rules can no longer be created or started.

- Empty matches are no longer stored in the report module's database.

- Objects with long names no longer cause presentational anomalies in the
  report module.

- Internal names of extracted resources are no longer shown in the report
  module.

- Apparently contentless matches corresponding to internal tasks are no longer
  shown in the report module.

- Sensitivity values set in the administration system are now correctly
  displayed in the report module.

- Office Open XML documents and traditional Microsoft Office OLE documents are
  now detected and handled more reliably.

Version 3.2.0, 16th March 2020
------------------------------

"Sensitive, Specialised, and Shiny"

New in this version:

- Administration system:

  - The login interface has been modernised with a new design.

  - The interface for creating and listing scanner jobs has been modernised
    with a new design.

- The scanner engine can now associate user-specified sensitivity values with
  rules.

  - The report module groups matches together based on sensitivity values.

- The scanner engine can now associate user-specified names with rules.

  - Compound rules will automatically be given a name based on their
    components.

- The report module now has support for special user roles.

  - Users can be assigned the special "remediator" role, which gives access to
    all matches not assigned to another user.

General improvements:

- The scanner engine can now handle timeouts and throttling.

- The report module now shows a more detailed name for all objects.

- All matches are now displayed in the report module, including matches found
  inside archive files and email attachments.

- System components can now communicate using a RabbitMQ server secured with a
  username and password.

Bugfixes:

- Tests for supported conversions now work properly again.

- Incremental scans based on modification timestamps now work properly again.

- Exchange Web Services mails with no subjects are now handled properly.

- The report module's user interface now looks as it should when viewed using
  Internet Explorer 11.

Version 3.1.0, 14th February 2020
---------------------------------

"Plug and Play"

New in this version:

- SAML support in the report module:

  - Users can now log in to the report module with organisational SSO.

  - Metadata provided by SAML identity providers can be used to relate users to
    matches.

- Initial support for scanning Exchange Web Services servers.

- The interface of the administration system has been modernised with a new
  design.

General improvements:

- The user interface now uses version 2.2.10 of the Django framework.

- The user interface is now consistently presented in Danish.

- The documentation has been updated for the 3.x series.

- Report module:

  - Files with several matches are presented more cleanly.

  - The user interface is correctly displayed with Internet Explorer 11.

- Scanner engine:

  - The old scanner engine has been entirely removed.

  - Formatted text is now processed more quickly and more reliably.

  - More image formats are supported for OCR.

  - Disk space usage has been reduced, and performance has been improved.

Bugfixes:

- Document metadata is now more relevant.

- Idle connections to network drives are now cleaned up more aggressively.

- It is now possible to log out of the report module cleanly.

- OCR is no longer performed on very small images.

- Copying file paths in the report module works properly again.

Version 3.0.0, 20th December 2019
---------------------------------

"Gift-Wrapped Under the Tree"

This is the first release of the 3.x release series of OS2datascanner.

New in this version:

- A new, extensible scanner engine:

  - Root privileges are no longer needed to mount remote network drives.

  - Elements in compound documents can now be uniquely identified.

    - Page numbers in PDF documents are tracked.

    - Full paths to files found in Zip files are now tracked.

  - Resources are only downloaded when needed and are immediately cleaned up.

    - Disk space requirements have been drastically reduced.

  - Support for scanning Office 365 mail installations.

  - Support for extracting metadata from scanned objects.

  - New sources of scannable objects can be added to the system.

- A new, extensible rule engine:

  - CPR rules and regular expression rules have been separated.

  - Logical operators (with short-circuiting) can be used to combine rules
    together.

  - New kinds of rules can be added to the system.

- A new scanner pipeline:

  - Scans are now performed by a pipeline of independent stateless processes
    which communicate by message passing.

    - All database interactions have been removed, drastically improving
      performance.

    - Scalability built-in: extra copies of any process can be started to
      improve performance.

  - Security:

    - Individual pipeline processes run in restricted sandboxes and
      do not have access to most system resources.

    - Scan results are filtered to avoid exposing sensitive information.

- A new report module:

  - The report module is now an independent component and not part of the
    administration system.

    - Users no longer need access to the administration system to read
      reports, reducing the attack surface of the administration system.

  - The interface has been modernised with a new design.

  - Flexibility: results from the pipeline are stored in the database in
    JSON format.

    - All results can be stored, even those not (yet) supported by the report
      module.

  - Targeted reports: users can now be shown only those results for which
    they have responsibility.

    - Support for associating metadata from scanned objects with users.

  - Historical results are stored.

  - Explanations are always available for why a file was, or was not,
    scanned.

  - Initial support for integrating external identity providers.

    - Support for assigning results to users based on Active Directory SID
      values.

- Reorganisation of the codebase for better modularity and code sharing.

- Integration with Prometheus for monitoring of performance and reliability.

- Structured logging for detailed information about internal system
  behaviour.
