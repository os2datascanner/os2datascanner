## Version 3.11.2, 10th August 2021

"README.1ST"

### New in this version

- An implementation manual for system administrators and project owners has
  been added to the administration system.

- It is now possible to exclude parts of a domain from a web scan.

### General improvements

- Digits present on different input lines are no longer grouped together when
  looking for CPR matches.

### Bugfixes

- The report module now ensures that matches with the same sensitivity and
  probability are also sorted by their primary key.

- Sitemap content-type parsing is now more robust.

- LDAP synchronisation is now more robust: user properties will now be updated,
  and users will be tracked properly even if their place in the hierarchy
  changes.

- The report module's collector process can once again understand the
  organisation update messages sent by the administration system.

## Version 3.11.1, 19th July 2021

This hotfix release improves the reliability of shared network drive
scanning by silently handling more exception types.

## Version 3.11.0, 15th July 2021

"OS2datascanner 3.11 for Workgroups"

New in this version:

-   Optional support for skipping super-hidden files:
    -   Files and folders on shared network drives marked as
        super-hidden can now be skipped.
    -   Super-hidden files are files marked with the *hidden* attribute
        and either the *system* attribute or a tilde at the beginning of
        their name. (This combination is often used by lock files and
        online backups.)

General improvements:

-   Requesting a scan for a LDAP organisational unit will now also
    include all units below it in the hierarchy.
-   The widget used to select LDAP organisational units and users is now
    larger.
-   The API server now supports scan configuration parameters.
-   The LDAP import process is now run on the server as a background
    task, improving responsiveness.
-   Conversions from rich text to plain text no longer replace sequences
    that include new lines and tabs with spaces, greatly reducing false
    positive matches from spreadsheets and HTML files.

Bugfixes:

-   LibreOffice processes can no longer escape timeout control.
-   The LDAP import process should no longer be interrupted by an
    internal server error.
-   The report module can once again display matches from web scans
    performed by early versions of OS2datascanner properly.

Notes:

-   The pre-Docker installation scripts are no longer supported and have
    been removed.

## Version 3.10.0, 30th June 2021

"Directory Enquiries"

New in this version:

-   Initial support for LDAP and Active Directory integration:
    -   Support for retrieving users from LDAP through Keycloak.
    -   Support for reconstructing LDAP hierarchies from distinguished
        names and from group membership.
    -   Support for adding and removing organisational units, employees,
        roles, and aliases in response to organisational structure
        changes.
    -   Microsoft Exchange scanners can now optionally retrieve user
        information from LDAP rather than requiring an uploaded list of
        users.
-   Initial support for runtime debugging:
    -   Pipeline components now respond to the `SIGUSR1` signal by
        printing a backtrace of the task they are presently carrying
        out. (The task is not otherwise interrupted.)
    -   Many components now emit progress and status messages to the
        system log.
-   Initial support for checking external links when running a web scan.

General improvements:

-   CPR context filtering is now performed as part of the test suite to
    avoid regressions.
-   Regular expression matches now also include a fragment of the
    surrounding context.
-   Certain Keycloak parameters are now automatically configured when
    the system is started.
-   The Docker development environment has been divided up into
    profiles, making it possible to run a specific configuration of the
    system.
-   The administration system's scanner status page can now show error
    messages and can delete status objects for failed scanner jobs.

Bugfixes:

-   The scan scheduling widget is now shown correctly in all situations.
-   Pagination fixes in the report module:
    -   Pagination with custom page sizes is now more reliable.
    -   When using custom page sizes, pagination controls now also work
        on the second-last page.
    -   Pagination now works when more than a thousand pages are
        present.
-   The Docker development environment should now also work correctly on
    recent versions of macOS.
-   Changes to the validation status of scanner jobs should now work
    correctly.
-   Sitemap files are now parsed with a more conservative XML parser.

## Version 3.9.6, 9th June 2021

This hotfix release corrects new matches not getting an alias relation.

## Version 3.9.5, 11th May 2021

This hotfix release corrects a performance problem typically seen when
CPR numbers are found in large documents and adds support for using
single sign-on systems with slightly incorrect system clocks.

## Version 3.9.4, 23rd April 2021

"Hundreds and Thousands"

New in this version:

-   Better pagination functionality in the report module:
    -   The pagination controls now match the rest of the user
        interface.
    -   Support for jumping to a specific result page.
    -   Support for changing the number of matches shown per page.
-   Preparatory work for LDAP and Active Directory integration:
    -   New model objects for tracking organisational units, employees
        and roles.

        (Note that preparatory LDAP objects are no longer shown in the
        Django administration system.)
-   Improved translations in the administration system.

General improvements:

-   Improved support for compressed sitemap files.
-   Improved support for HTTP referrer tracking.
-   The administration system's scanner status page now shows more
    historic scans.
-   The "remediator" role no longer overrides the normal display of
    matches in the report module.
-   More aggressive contextual filtering of CPR numbers.

Bugfixes:

-   The scanner engine's invocations of external tools no longer
    produce long-lived zombie processes in the system process table.
-   Encountering an unreadable directory will no longer interrupt the
    exploration of a shared network drive.
-   Scheduled scanner jobs are no longer run several times at once.
-   The API server once again produces extra scan information in the
    format expected by the pipeline.
-   Email notifications are now correctly translated.

## Version 3.9.3, 29th March 2021

This hotfix release fixes a missing timezone error when starting
scheduled scanner jobs.

## Version 3.9.2, 25th March 2021

This hotfix release fixes an error in a transitional migration that made
unsafe assumptions about the extra scan data sent to the report module.

## Version 3.9.1, 24th March 2021

"One Click Goes A Long Way"

New in this version:

-   Support for bulk handling of matches in the report module.
-   Improved the DPO and manager overviews:
    -   A new pie chart shows how many matches were found in each type
        of data source.
    -   A new calendar view shows how many matches were found in each
        month.
-   Preparatory work for LDAP and Active Directory integration:
    -   New model objects in the administration system to support
        multi-tenant installations with distinct organisational
        hierarchies.

        Note that these new model objects, shown in Django's
        administration pages under the "Management" (or, in Danish,
        "Administration") heading, should not yet be used in
        production environments.

General improvements:

-   The report module's age-based filter is now a true filter rather
    than a toggle: showing newer matches no longer hides older ones.
-   Much of the custom login management code has now been replaced with
    standard Django functionality.
-   Further unification of the user interfaces of the administration
    system and report module.
-   The number of worker processes that should be run by the
    administration system, API server and report module is now
    configurable.
-   Improved support for Internet Explorer 11.

Bugfixes:

-   The report module no longer fails when trying to present a match
    produced by version 3.6.0 or earlier of OS2datascanner.
-   The administration system's progress page no longer fails when a
    data source under scan could not be explored.
-   The cookies used by the administration system and report module no
    longer conflict with each other in development environments.
-   The DPO and manager overviews no longer produce error messages when
    a user is not logged in.
-   Fixed some deficiencies in the experimental Keycloak support.

## Version 3.9.0, 11th March 2021

"The Big Picture"

New in this version:

-   A refreshed user interface in the administration system.
-   Initial support for DPO and manager overviews:
    -   The report module now allows users in positions of authority to
        see selected statistical overviews of their organisation.
-   Experimental support for using Keycloak as a single sign-on system.
-   Support for assigning results in mail messages to users based on
    Microsoft Graph and Google Workspace metadata.

General improvements:

-   Metadata extraction is now fully integrated into the scanner engine,
    making it simpler to add new forms of metadata.
-   A new optional filter, switched on by default, now excludes matches
    newer than 30 days from being shown in the report module.
-   For statistical purposes, the report module now records the time
    when a match is marked as handled.
-   Drastically improved the performance of HTML text extraction.
-   Reduced the overhead in the API server's response messages when
    scanning embedded files.
-   Added indexes to certain commonly-used fields of the report
    module's database, drastically improving performance.

Bugfixes:

-   Batch migration of existing database objects no longer
    intermittently fails.

## Version 3.8.0, 8th February 2021

"Just Ask Nicely"

New in this version:

-   Support for calling OS2datascanner services from external systems:
    -   Added an API server that performs scans on demand.
    -   Added an API to the administration system that gives access to
        the defined rules and scanners.
    -   The Docker development environment now includes Swagger UI,
        which can be used to explore and experiment with the new APIs.

General improvements:

-   Initial support for translating the report module into other
    languages.

Bugfixes:

-   Improved the algorithm used to pair unpaired matches and metadata.

## Version 3.7.1, 1st February 2021

"Matchmaker"

General improvements:

-   Documentation has been restructured and improved.
-   Common requirements are now shared.

Bugfixes:

-   Matches and metadata were not always paired correctly:
    -   Due to a race condition caused by running multiple
        [pipeline_collector]{.title-ref} processes, only one is now
        allowed to run at a time.
    -   Lonely matches and lonely metadata objects created in error by
        previous releases will be paired up when deploying this release.
-   The service endpoint field is now optional when creating a Microsoft
    Exchange scanner. (If it is not specified, autoconfiguration will be
    used.)

## Version 3.7.0, 21st January 2021

"Pure Filtered Progress"

New in this version:

-   Support for checking the progress of a scan:
    -   The administration system now shows how many objects a scan has
        processed, along with an estimated completion time.
    -   The administration system prohibits a scan from being run more
        than once at the same time.
-   Support for filtering matches in the report module:
    -   Matches can now be filtered according to their organisation,
        sensitivity, and scanner.
    -   Many properties of matches have been moved out of unstructured
        storage and into the report module's database, drastically
        improving performance.

General improvements:

-   Several captions and labels in the administration system and report
    module have been made clearer.
-   Fields in scanner creation forms now include explanatory examples.
-   The administration system and report module now share and
    synchronise information about organisations.
-   Responsibility for checking the validity of a scan has been moved
    from the administration system to the scanner engine, improving scan
    startup time.
-   The report module now uses a single template to render all types of
    match, ensuring consistent display and functionality.
-   Fresh installations of the administration system now start with a
    default organisation and CPR number recognition rule.
-   Exchange Web Services API endpoints can now be explicitly specified
    when creating or modifying an Exchange scanner, adding support for
    servers that do not use EWS autodiscovery.

Bugfixes:

-   Sending email notifications and executing scheduled scans from
    Docker deployments is now more reliable.
-   User list files uploaded to a Docker installation of the
    administration system are no longer deleted at container shutdown.
-   The report module no longer speculatively collects result messages,
    improving performance and reliability.
-   The administration system is now rendered correctly for users with
    reduced privileges.
-   All characters can now be used in shared network drive passwords,
    not just URL-safe ones.

## Version 3.6.0, 17th November 2020

"Robotic Cloud Janitor"

New in this version:

-   Initial support for scanning Google Workspace organisations:
    -   Initial support for scanning Gmail accounts.
    -   Initial support for scanning Google Drive accounts.

(OS2datascanner is neither affiliated with nor endorsed by Google Inc.
or its partners or subsidiaries.)

-   A refreshed user interface in the report module.
    -   Matches are now paginated to improve browser performance.
-   Support for automatically handling matches:
    -   The report module will now automatically mark matches as
        "Edited" or "Removed" when objects have been changed or
        removed.
    -   If a transient problem arises when scanning an object, it will
        be added to the next scan and scanned again.

General improvements:

-   The scanner engine can now tell when objects have been deleted.
-   External processing tools can now be stopped automatically after a
    configurable timeout.
-   CSS updates are now correctly propagated to the report module in
    developer mode.
-   Required fields in the administration system's forms are now more
    clearly marked.
-   The report module's "Done nothing" resolution status has been
    replaced by "False positive".
-   The Docker development environment now also includes an (optional)
    simple SAML server for testing SSO support.
-   The Docker configuration has been tweaked and adjusted to better
    support cloud deployments.
-   Improved support for Internet Explorer 11.

Bugfixes:

-   Attempting to extract links from empty HTML pages no longer causes a
    web scan to stop.
-   Attempting to create a new Microsoft Graph scanner without a valid
    Microsoft application registration in place will no longer forward
    the user to a Microsoft error page.
-   Office documents whose HTML representation is above a configurable
    threshold are now automatically simplified before being processed.
-   Unsupported Exchange Web Services object types are now correctly
    ignored.
-   The report module no longer misrenders the name of the
    "Notification" sensitivity level.
-   Opening mails directly in the Microsoft Outlook desktop application
    should now be more reliable.
-   Forms in the administration system no longer display untranslated
    summaries of errors.

## Version 3.5.0, 14th September 2020

"Racing Green Shipping Container"

New in this version:

-   Initial support for Docker:
    -   The code has been refactored to better support containerised
        deployments.
    -   Installation-specific settings are now managed in a cleaner and
        more modular way.
    -   Support for Docker-driven development environments, including
        Prometheus-and Grafana-driven performance statistics.
-   Changes to the organisation of the scanner engine's pipeline:
    -   The three main components of the pipeline can now (optionally)
        run in a single process, improving cache efficiency and
        performance.
-   The report module can now give direct links to emails in the
    Microsoft Outlook desktop application, when the administrator has
    configured the network to allow this.

General improvements:

-   PDF file processing is now up to five orders of magnitude faster.
-   The terminology used in the administration system has been improved.
-   The report module now also sorts individual matches by probability.

Bugfixes:

-   Microsoft CDFv2 files that are not Office OLE documents are no
    longer processed as though they were.
-   The report module no longer presents an empty row when an
    alternative rule did not match.
-   Match handling for matches with large database identifiers is no
    longer unreliable.
-   The pipeline's components can now detect and recover from RabbitMQ
    connection problems during startup.

## Version 3.4.0, 21st July 2020

"New Worlds"

New in this version:

-   Initial support for scanning Microsoft cloud services through the
    Graph API:
    -   Initial support for scanning Office 365 organisational email
        accounts.
    -   Initial support for scanning OneDrive and SharePoint cloud file
        shares.
-   Initial support for scanning Dropbox accounts.

(OS2datascanner is neither affiliated with nor endorsed by Microsoft
Corporation, Dropbox, Inc., or their partners or subsidiaries.)

-   Support for context-sensitive result filtering:
    -   The CPR rule now supports filtering out matches that are likely
        to be Danish workplace identification numbers.

General improvements:

-   The administration system can now request permissions from external
    systems when creating scanner jobs.
-   The scanner job lists now highlight the type of scanner job being
    displayed.
-   The report module can now display the estimated probability that a
    match is a true positive (when this information is available).
-   Shared network drives are now also included in the test suite.
-   A common design language has been introduced for rule sensitivity
    levels.
-   Windows domains can now be inferred from fully-qualified DNS names
    when scanning shared network drives.

Bugfixes:

-   Uploading user lists to the administration system now works
    correctly again.
-   The administration system's rule description column is now
    correctly aligned.
-   The report module's support for SAML assertion encryption now works
    correctly with newer versions of the `pysaml2` library.
-   Building the user interface components no longer produces package
    management errors.

## Version 3.3.3, 24th June 2020

"Fit and Finish"

New in this version:

-   Scanner jobs, and their authentication information, can now be
    edited.
-   The report module now sorts CPR matches according to how likely they
    are to correspond to real CPR numbers.
-   The report module's SAML authentication code now supports assertion
    encryption.

General improvements:

-   The administration system now sends more detailed information about
    scans to the report module.
-   The structure of the scanner engine's internal messages is now
    defined more explicitly, allowing the test suite to notice
    discrepancies earlier.
-   The report module's sensitivity key can now be folded and unfolded.
-   The report module now also collects any error messages the scanner
    engine might produce during a scan.

Bugfixes:

-   System services are now correctly restarted when upgrading a
    production installation.
-   Disabling OCR image conversion now works correctly.
-   Matches in HTML email bodies are no longer reported twice.
-   Errors when opening data sources are now correctly handled.
-   Direct links to files in shared network folders should now also work
    for filenames containing non-ASCII characters.

## Version 3.3.2, 2nd June 2020

"Position of Privilege"

New in this version:

-   Support for special URLs:
    -   Administrators can now give OS2datascanner permission to use
        privileged URL schemes.
    -   The report module can now give direct links to files in shared
        network folders, when the administrator has configured the
        network to allow this.
-   `.eml` files, containing exported emails, can now be scanned.

General improvements:

-   The administration system now presents the result of attempting to
    start a scan more clearly.
-   The scanner engine now extracts metadata from files much more
    efficiently.
-   The scanner engine now automatically recovers from more transient
    communication errors.

Bugfixes:

-   Special folders, such as saved searches, are now excluded from scans
    of Exchange Web Services accounts.
-   The scanner engine will no longer restart components when attempting
    to send timestamps with no time zone from one component to another.
-   Communication problems between the administration system and the
    scanner engine no longer produce generic error messages.

## Version 3.3.1.1, 14th May 2020

This hotfix release removes some old debugging code from the component
that sends instructions from the administration system to the scanner
engine. (This code predated the completion of the scanner pipeline and
no longer serves any useful function.)

## Version 3.3.1, 14th May 2020

"You've Got Mail"

Neither the user interface of version 3 of OS2datascanner nor its
underlying scanner engine would have become as advanced as they are
without the efforts of Steffen Jørgensen and of Dan V. P. Christiansen.
The OS2datascanner development team thanks them for their many
contributions.

New in this version:

-   Support for handling matches:
    -   The report module now has a button for setting the resolution
        status of a match.
    -   Resolved matches are hidden from the user interface, but are
        preserved in the database for later reference.
-   Support for email notifications:
    -   The report module now has a command that sends email
        notifications of unhandled matches to all users.

General improvements:

-   All of the unused code in the administration system that was once
    responsible for interacting with the old scanner engine has been
    removed.
-   The appearance of the administration system's user interface
    elements is now changed when they receive focus.
-   Many modal dialog boxes have been removed from the administration
    system, giving a more contemporary feel.

Bugfixes:

-   The components of the scanner engine's pipeline no longer
    opportunistically prefetch messages, improving error resilience and
    scalability.
-   Scanning Exchange Web Services accounts should no longer produce
    occasional character decoding errors.
-   Errors in the metadata extraction process no longer cause all of the
    relevant file's metadata to be discarded.
-   Errors in external tools are now handled uniformly.
-   Encrypted files in Zip archives are now ignored instead of being
    unsuccessfully processed.

## Version 3.3.0, 24rd April 2020

"No Missing Screws"

New in this version:

-   Support for scanning websites:
    -   Results from website scans are displayed properly in the report
        module.
    -   Report module users can be given responsibility for matches from
        individual web domains.
    -   The scanner engine understands and follows links from sitemap
        and sitemap index files.
-   The report module's overview now includes a key that lists the
    various sensitivity levels.

General improvements:

-   The alignment of the user interface has been improved throughout the
    administration system.

Bugfixes:

-   The installation process now correctly builds CSS and JavaScript
    resources.
-   Files uploaded to the administration system are preserved when
    upgrading production installations.
-   The Apache configuration files built by the installation process no
    longer contain erroneous paths to installed files.
-   Drive letters associated with network drives are now correctly sent
    from the administration system to the scanner engine.
-   The administration system now correctly displays sensitivity values
    for CPR rules.
-   Attempting to delete a scanner job in the administration system no
    longer produces a broken modal dialog.
-   The report module no longer displays an unnecessary vertical
    scrollbar.

## Version 3.2.1, 3rd April 2020

"Direct Hit"

New in this version:

-   The report module now provides a direct link to matches in Office
    365 email messages.

General improvements:

-   The installation process now supports more kinds of deployment.
-   The scanner engine is now more resilient against internal
    communication problems.
-   The process of extracting plain text from documents with structure
    or formatting now produces more natural results.
-   Individual matches can now also carry sensitivity values for higher
    precision.

Bugfixes:

-   Scanner jobs with no associated rules can no longer be created or
    started.
-   Empty matches are no longer stored in the report module's database.
-   Objects with long names no longer cause presentational anomalies in
    the report module.
-   Internal names of extracted resources are no longer shown in the
    report module.
-   Apparently contentless matches corresponding to internal tasks are
    no longer shown in the report module.
-   Sensitivity values set in the administration system are now
    correctly displayed in the report module.
-   Office Open XML documents and traditional Microsoft Office OLE
    documents are now detected and handled more reliably.

## Version 3.2.0, 16th March 2020

"Sensitive, Specialised, and Shiny"

New in this version:

-   Administration system:
    -   The login interface has been modernised with a new design.
    -   The interface for creating and listing scanner jobs has been
        modernised with a new design.
-   The scanner engine can now associate user-specified sensitivity
    values with rules.
    -   The report module groups matches together based on sensitivity
        values.
-   The scanner engine can now associate user-specified names with
    rules.
    -   Compound rules will automatically be given a name based on their
        components.
-   The report module now has support for special user roles.
    -   Users can be assigned the special "remediator" role, which
        gives access to all matches not assigned to another user.

General improvements:

-   The scanner engine can now handle timeouts and throttling.
-   The report module now shows a more detailed name for all objects.
-   All matches are now displayed in the report module, including
    matches found inside archive files and email attachments.
-   System components can now communicate using a RabbitMQ server
    secured with a username and password.

Bugfixes:

-   Tests for supported conversions now work properly again.
-   Incremental scans based on modification timestamps now work properly
    again.
-   Exchange Web Services mails with no subjects are now handled
    properly.
-   The report module's user interface now looks as it should when
    viewed using Internet Explorer 11.

## Version 3.1.0, 14th February 2020

"Plug and Play"

New in this version:

-   SAML support in the report module:
    -   Users can now log in to the report module with organisational
        SSO.
    -   Metadata provided by SAML identity providers can be used to
        relate users to matches.
-   Initial support for scanning Exchange Web Services servers.
-   The interface of the administration system has been modernised with
    a new design.

General improvements:

-   The user interface now uses version 2.2.10 of the Django framework.
-   The user interface is now consistently presented in Danish.
-   The documentation has been updated for the 3.x series.
-   Report module:
    -   Files with several matches are presented more cleanly.
    -   The user interface is correctly displayed with Internet
        Explorer 11.
-   Scanner engine:
    -   The old scanner engine has been entirely removed.
    -   Formatted text is now processed more quickly and more reliably.
    -   More image formats are supported for OCR.
    -   Disk space usage has been reduced, and performance has been
        improved.

Bugfixes:

-   Document metadata is now more relevant.
-   Idle connections to network drives are now cleaned up more
    aggressively.
-   It is now possible to log out of the report module cleanly.
-   OCR is no longer performed on very small images.
-   Copying file paths in the report module works properly again.

## Version 3.0.0, 20th December 2019

"Gift-Wrapped Under the Tree"

This is the first release of the 3.x release series of OS2datascanner.

New in this version:

-   A new, extensible scanner engine:
    -   Root privileges are no longer needed to mount remote network
        drives.
    -   Elements in compound documents can now be uniquely identified.
        -   Page numbers in PDF documents are tracked.
        -   Full paths to files found in Zip files are now tracked.
    -   Resources are only downloaded when needed and are immediately
        cleaned up.
        -   Disk space requirements have been drastically reduced.
    -   Support for scanning Office 365 mail installations.
    -   Support for extracting metadata from scanned objects.
    -   New sources of scannable objects can be added to the system.
-   A new, extensible rule engine:
    -   CPR rules and regular expression rules have been separated.
    -   Logical operators (with short-circuiting) can be used to combine
        rules together.
    -   New kinds of rules can be added to the system.
-   A new scanner pipeline:
    -   Scans are now performed by a pipeline of independent stateless
        processes which communicate by message passing.
        -   All database interactions have been removed, drastically
            improving performance.
        -   Scalability built-in: extra copies of any process can be
            started to improve performance.
    -   Security:
        -   Individual pipeline processes run in restricted sandboxes
            and do not have access to most system resources.
        -   Scan results are filtered to avoid exposing sensitive
            information.
-   A new report module:
    -   The report module is now an independent component and not part
        of the administration system.
        -   Users no longer need access to the administration system to
            read reports, reducing the attack surface of the
            administration system.
    -   The interface has been modernised with a new design.
    -   Flexibility: results from the pipeline are stored in the
        database in JSON format.
        -   All results can be stored, even those not (yet) supported by
            the report module.
    -   Targeted reports: users can now be shown only those results for
        which they have responsibility.
        -   Support for associating metadata from scanned objects with
            users.
    -   Historical results are stored.
    -   Explanations are always available for why a file was, or was
        not, scanned.
    -   Initial support for integrating external identity providers.
        -   Support for assigning results to users based on Active
            Directory SID values.
-   Reorganisation of the codebase for better modularity and code
    sharing.
-   Integration with Prometheus for monitoring of performance and
    reliability.
-   Structured logging for detailed information about internal system
    behaviour.
