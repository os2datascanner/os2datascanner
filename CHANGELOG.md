# Changelog

## Next release

"Folie à Tous"

### New in this release

- Configuration of the support button is now done from the organization
  object, instead of as a environment variable.

- It is now possible to configure the support button further:

  - It is now possible to define the contact information of one singular DPO
    in the organization.

  - It is now possible to configure the name and contact information of the
    preferred support entity, both as an email address or a web address.
    
- UserErrorLog table from database can now be exported as a CSV-file.

### General improvements

- Previously seen error messages in the user error log are now hidden by
  default. They can be shown by checking the checkbox at the top of the page.

- General overhaul for Pie chart in DPO: 

  - Display tooltip on hover, and relative percentages are displayed alongside chart legends. 

  - Added and "empty" pie for empty datasets. 

- The loading time of the "completed scans"-tab has been improved by removing
  redundant logic from the view.

- Running `diagnostics --only Rule` in the admin module now also displays the
  scanners, which each rule is assigned to as an exclusion rule.

- The rule engine and its capabilities are now documented in some detail.

### Bugfixes

- When clearing the search bar on the user error log page, the table is now
  refreshed.

- Admins can now add users to Exchange- and Office365-scans.

- When the "Open" or "Copy" -buttons on the reportmodule are clicked, the last opened match
  will once again be highlighted. 
  
- In "My Overview", reverted matches are now counted correctly.

- Delete button for MSGraph mail matches is now visible on matches 
  whether HANDLE_DROPDOWN is enabled or not.

- Only notify of the number of new errors found during a scan in the subsequent
  email notification, if the USERERRORLOG-setting is toggled on.

- The OS2mo organisational import function is now less easily discouraged
  by unexpected errors.

- If a Keycloak access token runs out during user fetching, OS2datascanner will now fetch a new one
and proceed.

- The `diagnostics`-management command will no longer encounter a TypeError
  when aliases without accounts or users are present in the database.

- Adjusted left margin for content on smaller screens.

## 3.20.6, 2nd October 2023

"Purple Orchid in my Windowsill"

### New in this release

- A new simple diagnostics tool, which can be called as a management command.

  - Gives basic information about objects in the database.

  - Separate commands for the admin and report module.

  - Using the command in the report module gives information about the
    following objects: Account, Alias, OrganizationalUnit, Organization,
    DocumentReport, and problem messages on DocumentReports.

  - Using the command in the admin module gives information about the
    following objects: Account, Alias, OrganizationalUnit, Organization,
    UserErrorLog, and Rule.
    
- From this point on, it is only allowed to select one rule per scanner job.
  If one wishes to use combinations of rules, the rule builder should
  be used to create a new rule from existing ones.
    
- Added support in the report module for deleting Office 365 emails belonging to logged-in user. 

- A new replacement for the Health Rule has been added.
  This rule is simpler and promises far greater scanning speeds.

### General improvements

- Users will now only ever be able to see data from their own organization
  when accessing the DPO overview.

- The UserErrorLogView is now hidden by default. This can be toggled by a
  configuration.

- The scan status tab in the admin module now issues no duplicate queries to
  the database, and prefetches related scanners.
  
- Performance has been improved in the report module.

  - The number of queries has been greatly reduced, and is now constant
    regardless of the number of results.

  - An index has been created on the "only_notify_superadmin"-field on the
    DocumentReport model.
    
- The OrganizationalUnit overview is now considerably faster.

- The user manual for the report module, has been updated to match the current
  version of the system
  
### Bugfixes

- Scannerjobs for Exchangescanner won't start until validation is confirmed

- Users in the report module can now be granted superuser status from the
  admin module through their connected Account object.

- The loading time of the UserErrorLogView is now considerably faster, as both
  the ScanStatus and Scanner relations are prefetched.
  
- The mini-scanner now enforces server-side validation of the file size restriction.

- Workers no longer freeze during status message preparation if the object's
  metadata is not available.

- Re-examining a spreadsheet scanned with version 3.20.4 or older of
  OS2datascanner will no longer fail with an unsupported format error.

- UserErrorLog-objects no longer arbitrarily change sorting when changing page.

- Matches found in an Exchange mail account that is later deleted will now be
  correctly treated as though they had been deleted.

## 3.20.5, 11th September 2023

"Mo' Code Less Problems"

### New in this release

- Functionality for manually cleaning up stale accounts in the admin module.

  - Scanners with stale accounts now display a warning in the UI.

  - Users in the admin module can choose which stale accounts to clean up
    reports for, and which to leave as is.

- Access to the DPO-overview in the report module is now based on Position-
  objects with the "data protection officer"-role, instead of the DPO Role-
  object, which has been removed.

- Excel and Spreadsheet-like files will now be processed with pandas.DataFrame
  and present a match with a precise location including sheet and row.
  
### General improvements

- The pipeline will stop execution of a rule component after it has produced
  (by default) ten matches, reducing the memory usage and total message size
  and improving performance.

- Scheduled execution of scans should be more robust, both in the user
  interface and in the backend service (and, if the latter goes wrong in some
  way, it can now print informative debugging information).

### Bugfixes

- Result collector is now more robust if encountering identical problem messages.

- The estimated time of completion of scannerjobs no longer breaks, if the
  ScanStatus only has one snapshot.

- Adjusted shadow effect for visualizing scrollability on tables in the admin 
  module, ensuring compatibility with Safari browsers.

- Undistributed reports from the same scannerjob with differing scan_times
  will no longer cause multiple instances of the same scannerjob in the
  overview of undistributed scannerjobs in the report module.

- Web scans now use heuristics to detect files that have been deleted but which
  do not produce a `4xx` error code.

  - Suggestions for further heuristics to add are welcome; this function is new
    and by no means complete.

## 3.20.4, 16th August 2023

"To Prevent Arthritis"

### New in this release

- It is now possible to scan files shared through Microsoft Teams. 

- Removed expressions, "generelt" and "diverse", from HealthRule.

- The Pipeline has received an overhaul with respect to the use of RabbitMQ,
  such that workers can be assigned to serve a dedicated organisation.
  Thus, for a system we multiple workers and organisations, it is possible
  to run multiple scanner jobs in parallel.
  
- It is possible to (globally) turn on GhostScript-compression for PDF-files.

### General improvements

- Added a related name to the ScanStatusSnapshot model.

- Added footer with current version to admin and report modules.

- Removed sortByHandlers.js and formatted caret buttons to use HTMX instead 
  of hmtl + js.

- The unused "expression" column has been removed from the table on the rules page.

- The DPO- & Leader-overview's OrganizationalUnit dropdown is now ordered alphabetically.

### Bugfixes

- Tooltips for overflow titles in the report module are now correctly displayed.

- The `count_matches_by_week`-method on the `Account`-class has been 
  refactored, and is more robust towards missing created_timestamp-values on
  related DocumentReports.

- Logging in with SSO now works with more than one organization in the database,
  as long as the user's account already exists.

- Ordering by match count in the leader overview now reevaluates match counts 
  for all accounts, without having to scroll to the bottom of the page first.

## 3.20.3, 3rd August 2023

"Check My Scans"

### General improvements

- Temporary errors produced when checking a match again are now displayed as a
  warning in the report module.
  
- The `start_scan` management command has a new convenience parameter for
  starting (partial or complete) scans that do not enforce the last
  modification date check.

- The manual in the admin module is now hidden by default. The visibility of
  this page can be configured in the pillar settings.

### Bugfixes

- Transient errors in retrieving object metadata will no longer cause the
  pipeline to conclude that the object no longer exists.

- The administration system can now automatically resolve completed scan
  statuses that have become stuck due to a small number of missing status
  messages.

- Scan statuses can no longer disappear from the list of completed scans by
  reporting themselves to be more than 100% complete.

- Manually created Position objects for users in units they are already members of, can now
  coexist with imported ones.

## Version 3.20.2, 11th July 2023

"Blasting Off at the Speed of Light 🚀"

### New in this release

- The organizational unit overview is now cleaner and prettier in a table.

- Initial support for caching:

  - OS2datascanner can now maintain a disk cache of the results of its
    conversion operations.

  - Converted forms can be retrieved from the cache almost instantaneously,
    making it much easier to iteratively test and improve rules.

  - Cached representations are compressed and encrypted: a 13 megabyte PDF
    file with many embedded images, for example, uses approximately 50
    kilobytes of cache space.

- Support for filtering by organizational units in the DPO overview.

- Support for automatically refreshing expired OS2mo access tokens.

### General improvements

- Considerable perfomance improvement in the DPO-overview (about 90% faster 
  database interaction).

- Rows in the leader overview are now loaded dynamically as the user scrolls.

- Improved the test suite by adding tests for the rule-related views.

### Bugfixes

- Gracefully stopping the RabbitMQ communication background thread no longer
  prints an alarming error message.

- Dead URLs are now presented in the error messages.

- Improved the test suite by adding tests for the rule-related views.

- OS2mo import jobs now print more debug information to the log if they receive
  an invalid response.

- The second and subsequent scans of a PDF file no longer unconditionally
  download the file to check its authoring timestamp.

- The second and subsequent scans of an office file no longer perform
  unnecessary conversion tasks to compute filenames.

- Hovering over a data point in a line chart once again displays its value in a
  tooltip.

## Version 3.20.1, 22nd June 2023

"Artificial CEO"

### New in this release

- It is now possible to view and sort reports by the age of the scanned resource. When the screen is wide, it remains a caret, but on smaller screens (i.e. smartscreens) the sort options becomes two buttons at the top of the page. 

- Support for simple scans in the administration system:

  - It is now possible to upload individual files to the administration
    system and to view the results of executing a rule on them.

  - This feature is useful for rapidly prototyping rules prior to running a
    full-scale scan.
    
- The "Archive"-tab returns!

  - This tab has three sub-tabs for personal, remediator and undistributed
    results.

### General improvements

- Guesses for the end time of running scannerjobs can no longer be in the past.

- OS2mo import job now use graphql API endpoint v7 and has configurable pagination size.

- New retry logic for OS2mo import.

- Python upgraded to version 3.11.3

- `urls.py` import statements have been further prepared for Django 4.2.

- New management command added: `setup_org`, to ease the process of setting up new installations.

### Bugfixes

- Resolution timestamps are now correctly set whenever a result is automatically
  handled.

- Matches handled more than a year ago are no longer erroneously ignored by the
  DPO overview's trend graphs.
  
- Deleting or marking an error message in the admin module as "seen" now
  correctly refreshes the table of error messages.

## Version 3.20.0, 2nd June 2023

"Quick Brown Fox"

### New in this release

- The report module views have been refactored

  - Reports are now presented in their own subpage, depending on their origin;
    Individual reports, remediator reports and undistributed reports.

  - The button to access the archive has been moved to a submenu in the report
    module main page.

  - The report module is now approximately 20 times faster.

- It is now possible to search for substrings in the error message and path of
  user error log objects in the usr interface. Matched substrings are also
  highlighted for ease of reading.
  
- Error logs can now be sorted by name, start time and path.

- Users can now create "rulesets" instead of regex rules in the "Rules"-tab
  in the admin module.

  - Rulesets are a more flexible way of combining rules, allowing for AND, OR
    and NOT operators between them.

  - This change allows combining preexisting rules and custom regex rules,
    for example, it is now possible to create a rule that matches a file if it
    contains both a CPR number *and* a name.

### General improvements

- The `SIGUSR1` backtrace function is now extensible, allowing components to
  provide more information about what they're doing.

- The background job runner process now also shows information about the
  current job when it receives the `SIGUSR1` signal.

- Associating email aliases with matches is now several orders of magnitude
  faster.

- While scanning, a more qualified guess for the runtime of the scan is now
  displayed on the "scanner status"-tab.

- Access to the leader overview tab can now be configured on the Organization
  model.

### Bugfixes

- More robust datetime parsing for calendar matches.

- The timeline chart in the completed scans tab now correctly show axis labels
  and do not show an irrelevant legend.
  
- The leader tab now shows the correct number of employees for a manager.

## Version 3.19.3, 12th May 2023

"Bulking Agent"

### New in this release

- The `makefake` management command now works once more, and it is now
  possible to set the "owner"-field of the generated reports through a
  command option.

### General improvements

- Slight improvement to performance in the report module by only querying for
  the fields which are needed.

- Models inheriting from "core_organizational_structure" now conform to use the same datatype
  for their primary key in the Admin & Report modules.

- Serialization logic has been refactored, for better maintainability and
  support for bulk serialization.

- LDAP-, MSGraph- and OS2Mo-ImportJobs now share more infrastructure and 
  all support bulk operations.

- "event_collector" has been reworked to support bulk operations, and refactored to significantly reduce
  its complexity and responsibilities.

- "Account" now has a manager-class, responsible for corresponding User objects.

- The pie chart showing distribution of sensitivities has been removed from the
  DPO overview.

#### Bugfixes

- No longer are DocumentReports created for missing objects of no relevance.

## Version 3.19.2, 21st April 2023

"Hairstylist of the Year"

### New in this release

- Access to the manager overview is now granted dynamically based on
  organisational information and not on the static `Leader` role, which
  has been removed.

- The number of matches marked with "only_notify_superadmin" are now shown
  separately in the leader overview for each user.

### General improvements

- Navigating to a section in the manual now highlights the header of that 
  section.

- In the leader overview, usernames are now shown below employees names.

- Major performance improvements in the leader overview.

### Bugfixes

- DocumentReport objects with missing `created_timestamp` values have had that
  value set equal to its `scan_time` value.

- Revisiting Microsoft Graph emails with matches now works reliably again.

## Version 3.19.1, 12th April 2023

This minor release fixes a potential crash triggered by scanning certain
compound document formats with the new home folder flag set

## Version 3.19.0, 4th April 2023

"Automatic Egg Roller"

### New in this release

- Special support for scanning home folders:

  - Traditional file scans now have a flag that indicates that the folder to be
    scanned is the parent of users' home folders.

  - When this flag is set, the owner of a home folder is given responsibility
    for everything in it, even files that they do not technically own.

- On top of the already-existing organisational unit manager role, Accounts can
  now declare that a specific person is their line manager. (This information
  is presently only available when importing data from Microsoft Graph.)

- The next scheduled scanjob of a scanner is now shown on the "scanners"-page in the admin-module.

- In the report module a superuser can search for a scan job to distribute if there is more 
  than 10 undistributed scanner jobs.
  
- In the report module a superuser can search for a scan job to distribute.

- Management command "cleanup_account_results" for deleting all document
  reports associated with a given account and scanner job from the admin 
  module.

- It is now possible to configure the admin module to automatically initiate a
  cleanup of DocumentReport-objects in the report module after each succesful
  import job.

  - The process will delete all DocumentReport-objects associated with
    accounts, which are no longer covered by the scanner jobs they were found
    by.

- Usernames of employees are now displayed in the leader overview, and it is
  possible to sort by usernames.
  
### General improvements

- Scanner objects now contain information about which accounts they cover,
  which can be used to identify when an account is no longer covered by a
  scannerjob.

- Employees in the leader overview are now sorted by first name by default.

### Bugfixes

- Danish translations are no longer hardcoded in scanner model fields.

- Paths in the administration system's error log can no longer overflow their
  table cell and make neighbouring content hard to read.

- OS2mo import jobs will now ignore empty manager-objects in the imported 
  structure.

- When importing from LDAP, Alias and Positions objects are no longer deleted when created manually.

## Version 3.18.8, 21th March 2023

"Shaka brah! 🤙"

### New in this version

- Experimental support for extra hints in web scans:

  - OS2datascanner can now extract `<title />`s from web pages and can use
    these when presenting matches.

  - Websites can now indicate that their links correspond to some other URL.
    When this is used, the report module will display that other URL instead.
    (This provides a better experience when using a proxy server to scan an
    external system's content.)

### General improvements

- The documentation for the web scanner has been greatly expanded.

- It is now possible to hide the archive-tab through a configuration variable.

- Sizes of the widgets in the DPO statistics overview fit their content better.

### Bugfixes

- Choosing a scannerjob in the DPO statistics overview now loads the correct
  figures.

- OS2mo-import no longer cancels import-job due to the size of the organization
  it pulls from.

- Removed duplicates caused by both having an employee- and manager-role in the same Org_unit.

## Version 3.18.7, 13th March 2023

"Island Troubles"

### Bugfixes

- An issue where scanning calendar events would not work properly has been fixed.

- Reigned in a migration, that could accidentally delete document reports.

- The personal statistics view in the report module now works correctly for
  all users, not just those with explicitly defined roles.

## Version 3.18.6, 8th March 2023

"Iterative Bugfixing"

### Bugfixes

- The "path"-field of the DocumentReport is now altered in a separate
  transaction to the rehashing population function.

## Version 3.18.5, 7th March 2023

"Hash Browns"

### Bugfixes

- The "path"-field on DocumentReport objects are now hashed, so the unique-
  constraint index does not throw an error on too large strings. The field
  is changed to a character field once again.

## Version 3.18.4, 6th March 2023

"Index Schmindex"

### Bugfix

- Corrects an issue with a database index on DocumentReport path-field for some installations.

## Version 3.18.3, 24th February 2023

"Idle Chitchat"

### New in this release

- Support for reducing HTTP communication:

  - Web scanners can now be configured to aggressively reduce the number of
    HTTP calls they make to the server.

  - OS2datascanner now supports a sitemap extension that declares the content
    type of each URL, reducing the number of HTTP calls needed under the
    conversion process.

### General improvements

- All scanners are now always sorted alphabetically in the scanner lists.

### Bugfixes

- Background jobs now only request confirmation from RabbitMQ once they're
  finished and not after every message.

- Resolution time for previously handled document reports now gets removed if the document report gets reverted.

- Fixed overlapping numbers in the user overview.

- When handling matches while the distribution element is on the page in the
  report module, the handling animation now gets to finish.

## Version 3.18.2, 15th February 2023

"Quick Fact Check"

### General improvements

- DocumentReport's now store "owner" in a separate, indexed, text field. 
  Thus allowing for faster database lookups, greatly improving page-load performance when result-relations are evaluated.

- The four varieties of collector process now also support the `SIGUSR1`
  signal, printing a backtrace when they receive it.

### Bugfixes

- Users without an associated `Account` object can once more log into the
  report module.

## Version 3.18.1, 10th February 2023

### Bugfixes

- Fixed an issue where the `crunch`-function would return strings too long for
  the `path`-field in DocumentReport objects.

  - The `path`-field now accepts strings of arbitrary length.

## Version 3.18.0, 9th February 2023

"Naturwissenschaften"

### New in this release

- A page has been added for a personalized overview of the user's resolution
  pattern. This overview is identical to the one accessible in the leader
  overview. This page can be accessed through a button in the header menu.

- Major changes to the way organizational units are presented:

  - Units are no longer shown on the "organizations"-tab, but rather on their
    own page, which is accessed through the "organizations"-tab.

  - Units can now be filtered through a search field, and root units with
    no associated accounts are hidden by default.

  - Users are now able to add and remove managers to and from their 
    organizational units.

  - Units are now paginated for increased performance.

  - Units are now sorted alphabetically.

  - Users are able to see folder structure and owner for Msgraph-file scans.

### General improvements

- The documentation for the scanner engine has been updated.

- The documentation now describes more of OS2datascanner's supported data
  sources.

- The uniqueness identification method has been refactored to allow a higher
  degree of control, and to prevent creation of duplicate DocumentReports
  in the report module.

- Increased efficiency of certain database queries made from the report module, improving page load time.

- The start time matched calendar event is now shown on the report module for
  MSGraph Calendar scans.

- RabbitMQ clients that do not actually react to dynamic instructions from
  the administration system no longer register themselves to receive them.

- Results from MSGraph based file scans can now be opened with the open-button. 

- Added tests for organization views.

- Refactor of the support button to slightly improve performance.

- Support button now opens on hover instead of focus.

### Bugfixes

- Hovering over the handle button will no longer obscure it with an invisible
  element.
  
- On small screens, the buttons on the sidemenu in the admin module are no
  longer overflowing off-screen.

- Email attachments which declare URLs or relative paths to be their filename
  are now handled correctly.
  
- Fixed an issue where any user was able to add and edit organizations for any 
  client.

- The administration system's signal handlers now pause until their event
  broadcasts are acknowledged, making these broadcasts much more robust.
  
- URL kwargs are no longer appended when using the "Open" and "Copy" buttons
  in the report module.

- Profile page in report module can now be accessed by users with no roles.

- While importing organizational structure on the "organizations"-tab, only the
  relevant table column is now updated dynamically by poll, instead of the
  entire table.

## Version 3.17.9, 23rd January 2023

"4.3 Billion Index Cards"

### General Improvements

- Office 365 mail scans now evaluate last modified dates by sent time, except for draft emails.

### Bugfixes

- An optimised database index has been added for the checkup collector
  component of the administration system, greatly improving its performance.

## Version 3.17.8, 17th January 2023

"What Time Is It?"

### Bugfixes

- Corrected for the introduction of EWSDateTime in exchangelib. Such object can now be made
 navigable.

## Version 3.17.7, 11th January 2023

"A Wizard is Never Late ... Nor is he Early."

### New in this release

- Scannerjobs now start at 19:00 and later, instead of 18:00.

- Ad import jobs now start at 17:00 instead of 00:00.

- A superuser can now, in the leader overview, delete all results stemming from
  a specific scannerjob for individual users.

- By default, Office 365 mail scans will no longer scan users deleted post folder. Inclusion of
  deleted post folder can be turned on in the scanner settings.

### General Improvements

- Superusers in the report module can now access all organizational units in
  the leader overview.

- Duplicate position-objects are no longer allowed.

### Bugfixes

- Mail content can once again be reliably retrieved using the Exchange Web
  Services protocol.

### Other notes

From the 31st of December 2022, Exchange scanners cannot be used to scan
Exchange Online, as Microsoft has deprecated the legacy authentication
mechanism used by OS2datascanner. For now, we recommend the use of a Microsoft
Graph scanner instead. (On-premises customers are not affected by this change.)

## Version 3.17.6, 6th January 2023

"Einstein Failed Math"

### New in this version

- Support for API scans of individual objects.

### Bugfixes

- A method on the Account object will no longer divide by zero.

- Editing file, web and Exchange scanners works properly again.

- Fixed a migration's assumption that the `scan_time`-field would always
  exist on DocumentReport objects.

### Other notes

It is a common misconception, that Einstein failed at math. In reality, he was
a bona fide genius, and excelled at advanced math even as a child.

## Version 3.17.5, 4th January 2023

"Stream a Fire Pit on your Favourite Streaming Service"

### General Improvements

- The URL field in the Exchangescanner and Filescanner forms are now correctly 
  marked "domain" and "unc" instead.

  - Some unused calls to empty URL fields have been removed.

- The "copy" and "copy folder" buttons now have the text "copy path" and "copy 
  folder path" instead, and have been moved to below the path instead of below
  the name of the report.

- Light grey text is now slightly darker for higher contrast and readability.

### Bugfixes

- Trying to import users with deprecated emails no longer breaks the import 
  job.

- The completed scan overview no longer breaks, when it encounters ScanStatus
  objects with no ScanStatusSnapshots.

- An issue where some missing fields on document report objects could break the
  report_event_collector process has been fixed.

- A localized primary key in the HTML has been correctly *unlocalized*.

- Fixed the sizes of some responsive buttons.

## Version 3.17.4, 19th December 2022

"Cinnamon; 'Tis the Seasoning"

### New in this version

- The leader overview is no longer the same as the DPO overview; Instead, the 
  leader overview now contains an overview of all employees in the leader's
  organizational units, showing useful information:

  - Total unresolved matches.

  - Different statuses depending on the user's resolution pattern.

    - "Finished" for users with no current matches.

    - "Accepted" for users who have handled at least 75% of the amount of new 
      matches they received in the last 3 weeks.

    - "Not accepted" for users with who have either not handled any matches in 
      the last 3 weeks, or have handled less than 75% of the amount of matches 
      they received in the last 3 weeks.

  - Chart of user's resolution pattern for the past year.

  - Button for easily sending reminders to the user.

- A modelclass for storing sizes of files now exist

### General Improvements

- Status timeline charts are now only drawn when needed, considerably boosting
  performance while viewing completed scans.

- The entire button can now be clicked in the header menu in the report module.

- The use of "results" and "matches" in the report module is now more consistent.

### Bugfixes

- Pagination options on the "error log"-tab now correctly lead to pages on the same tab.

- Marking an error log as seen is now more smooth, and does not move the entry around.

## Version 3.17.3, 7th December 2022

"Mo' Managers, No Problems"

### New in this version

- It is now possible to import organizational structure from OS2mo.

  - This import type functions like other import types in OS2datascanner (LDAP,    MSGraph), and populates the database with organizational units, accounts and aliases.

  - In addition, this import is also able to import the _position_ of each imported user, which is set in the "position" through-table.

  - Only one import type can be active at a time.

  - Instructions for setup can be found in the dev-environment.md file.

### Bugfixes

- "Completed scans" now correctly display charts after the first 1000 scans.

- Microsoft Graph account discovery is now more robust against unexpected states.

## Version 3.17.2, 2nd December 2022

"Bugs Bunny"

### Bugfixes

- /status-completed no longer crashes, if some ScanStatus objects do not have Snapshots.

## Version 3.17.1, 1st December 2022

"Catchy Title"

### New in this version

- The side menu in the report module has been removed, and the menu items have instead been moved to the header. For small screens, the functionality is unchanged.

- A timeline of a completed scan can now be seen on the "Completed scans"-tab.

- UI for analysis tool included as a new page and new feature in the admin module. The feature is disabled by deafult

- A manual can now be found in the report module under /help.

- A service button has now been implemented in the report module:

  - A large button with a "?"-symbol is always placed in the lower right corner
    of the report module. This feature is off by default.

  - Clicking the button will show up to five options:

    - "Manual", a link to the manual page.
    
    - "FAQ", a link to the FAQ part of the manual page. Hovering will also
      display links to the specific questions.
    
    - "Contact DPO", hovering will display a list of users with the DPO role,
      which have the "contact person" option enabled on their profile. Clicking
      one of the users will open the user's preferred mail client with contact 
      info on the DPO.
    
    - "Contact IT", opens the user's preferred mail client with contact 
      info on the user's organization.
    
    - "Contact Magenta", opens the user's preferred mail client with contact 
      info on Magenta ApS's support line with prepopulated data from the user's 
      current view.

### General Improvements

- Release notes are now written gradually, instead of in batches during release procedures.

- When handling a result in the report module, the animation will now get to finish before the DOM content is swapped.

- Added string representations to some models without for easier debugging.

- Functions for drawing charts and graphs refactored.

- Better UI for the report module when browsing from large tablets.

- More info on document reports in django admin added.

- The name rule can be made less aggressive, reducing false positives.

- When scanning for dead links in webscans, links will only be matched if they return either a 404, 410, 421, 423 or 451 status code.

- Worker processes clean up their temporary files more aggressively.

- Email notification logic refactored. Command now has more flags available for testing purposes and email text now gives recipient more details.S

### Bugfixes

- Adjusted media root to support profile images uploaded by the user.

- Path is shown correctly when editing Office 365 scannerjobs 

- "Completed scans" table now has a column showing number of results found in associated scan

- Pagination options now work in the admin module.

- Time stamps are now correctly set when resolving a match result.

- Sensitivity values are once more displayed for name, address and regular expression rules.

- Contexts are now also shown for name and address rule matches.

- CPR number-like strings are now pruned more aggressively from all match contexts.

- Automatic match handling is now enabled again for LibreOffice and PDF documents.

- Certain sensitive internal operations are now exempted from timeout control.

- Scannerjob timestamp for last modified is now based on last successful run's start time for better accuracy.

- The explorer process is now correctly logged.

## Version 3.17.0, 31st October 2022

"Refreshed Rabbit"

### New in this version

- Back-end support for running a checkup-only scan:

  - Administrators with command-line access to OS2datascanner can now ask for
    all objects containing matches from a previous scan to be re-examined. (A
    user interface for this functionality will be introduced in an upcoming
    release.)

- Initial support for creating custom rules:

  - Superusers can now create advanced rules using boolean expressions in the
    Django administration pages of the administration system. (This
    functionality will be exposed to other users in an upcoming release.)

- OS2datascanner now uses RabbitMQ v3.11 where available, bringing enhanced
  performance and more features.

### General improvements

- RabbitMQ now saves messages to disk as soon as possible, reducing its memory
  requirements for large queues and improving reliability.

- The error log view now supports the same functionality as the scan status
  view.

- The report module now displays an indicator when waiting for a response from
  the web server.

- Both the full path and the path to the containing folder can now be copied
  for matches in shared network drives.

- The collector processes used to receive information from the scanner engine
  have been split up and simplified, improving performance.

- Transmitting imported organisational information from the administration
  system to the report module is now approximately a hundred times faster.

- Managers and DPOs can now also see an overview of the resolution status of
  matches.

- Images will no longer be extracted from PDF files and ignored when running a
  scan with the OCR function disabled.

### Bugfixes

- Statistical overviews no longer show data sources for which no data was
  scanned.

- Deleting a scan status object is no longer extremely time-sensitive.

- URLs are now presented more usably by the report module.

- Handling a match in the report module no longer resets the chosen display
  properties.

- The report module no longer treats the manager and DPO overviews as being
  equivalent in some circumstances.

- OneDrive and SharePoint files are now correctly assigned to the users who own
  them.

- Marking a file that contains matches as unreadable no longer makes those
  matches "sticky" in the report module.

## Version 3.16.1.5, 7th October 2022

"You Shall Not Pass"

### Bugfixes

- The "Scanner Status"-tab no longer breaks when accessed by a non-superuser.
- The report_collector process will no longer crash when encountering an IntegrityError.

## Version 3.16.1, 5th October 2022

"Just Read the Instructions"

### New in this version

- The "Error messages"-tab in the "Scanner status"-tab now shows the number of new messages in a notification bubble.
  - New messages in the "error messages"-tab are also highlighted, and has an adjacent bubble with the text "NEW".
- "Handle"-buttons can now be changed to dropdowns with a number of choices for the method of handling used.
- Previous scans in the "Completed scans"-tab can now be removed.
- The report module now presents a SAML metadata file for easy setup of SSO access.

### General Improvements

- Prettier checkmarks added to user page.
- Running the `quickstart_dev`-command now gives the dev-user an account-object and assigns an organization.
- Results in the report module are now sorted by sort_key _and_ primary key.
- All functionality from UserProfile-objects have now been moved to Account-objects.
- More information is presented in some django-admin tables.
- Error log messages are now sorted by scan time _and_ primary key.

### Bugfixes

- Images in media/images-folder are now ignored by git.
- Import jobs which are suddenly stopped now correctly have their state changed to "FAILED".
- The sort_key for MSGraph mail handles are now set correctly, and includes folder and subject field.
- Duplicate aliases are now routinely cleaned up, and cannot be created.
- Some HTMX elements now correctly send POST-requests instead of GET-requests.
- The "Go to" button in the report module now works again.

## Version 3.16.0, 15th September 2022

"The Changing of the Guard"

### New in this version

- Opened matches are now highlighted in the report module for easier identification when returning.
- Error logs can now be removed from the UI.
- LDAP based organizational imports now also trigger synchronization of data to the report module.
- Manager and DPO statistics can now be filtered by scannerjob.
- Run scanner modal now includes a direct link to scan status enabling a more fluid user flow.
- Support for user profile images.
- Email notification interval can now be configured on an organizational level in the admin module.

### General Improvements

- 'Distribute' button is now disabled when no scannerjob is selected.
- Sidebar and top navigation path properly display location in the admin module, when configuring MSGraph related functionality.
- Manager and DPO statistics dropdown menu now use HTMX for dynamic page updates.
- 'Clear' buttons in the report module are now dynamic.
- Sorted out broken links in project documentation.
- Engine containers can now be configured with environment variables.
- Reworded help-text in popup upon handling matches for more consistent terminology.
- MSGraph related documentation updated.
- The PostgreSQL container now has 256MB of shared memory, as recommended by upstream.
- Icons for match sources now display a text when hovering for easier identification.
- DocumentReport's organization field is now properly filled.
- Matches now properly rely on DocumentReport's organization field in the match assignment process.

### Bugfixes

- In cases where HTTP HEAD requests are not supported, a fallback of HTTP GET is now in place.
- Checked boxes no longer stick around in the report module upon page refresh.
- Password reset links now work correctly in the report module.
- Address- and Name-rule matches can now be displayed in the report module again.
- API server kept up-to-date, by including previously missing filter_rule.
- HTMX related triggers are now properly retrieved through headers.
- WebResource's get_size method is again functional.
- Corrected behind-the-scenes JavaScript error occurring when a user had no matches.
- Superusers can now create multiple importjobs when multiple organizations exist.
- Faulty translations corrected.

## Version 3.15.6, 18th August 2022

"The Second Favourite Child"

### New in this version

- The user page in the report module has a new improved look.

- Distributing withheld matches can now be done for one or more chosen scannerjobs.

- Users now have to confirm their choice, when handling a match for the first time in two days.

### Bugfixes

- Now passing all user information to the dropdown menu logic.

- Grey-out functionality extended to rules.

- Matches on mail objects with no folder information now displayed correctly in report module.

- Importing an invalid user no longer stops the import job. The user is skipped instead.

## Version 3.15.5, 11th August 2022

"Here Comes the Drop!"

### General Improvements

- On the user page, the username is now displayed in the title if no short-form name is available.

### Bugfixes

- The dropdown menus in the report module now work again.

## Version 3.15.4, 9th August 2022

"Respect My Authority!"

### New in this version

- Number of error log objects found during scan is now included in the mail summary.

- When only one option is available in a dropdown menu, that option is automatically selected, and the dropdown is disabled.

- Filtering options in the report module are now much more intuitive and easy to use.

  - When an option is chosen, other options are now still shown in the dropdown menu.

  - The number of matches of a given filtering option accurately describes how many matches will be left when switching to that filtering option.

- Users in the report module can now see the information associated with their account on a user profile page.

- Created import jobs via MSGraph are now automatically run every day at 00:00.

- The report module now only loads the first 10 matches of each match report. More matches can be loaded with the new "show more matches"-button.

- When pressing the "Open", "Open folder" or "Copy"-buttons in the report module, a time stamp is now added to the report, to keep track of when it has been accessed. This timestamp is shown on the report in the report module.

- OS2datascanner now remembers your credentials when connecting to your Microsoft account. It is no longer required to log in more than once.

### General Improvements

- The complex `SingleResult` and `MultipleResult` classes have been removed.

- Redundant path fragments have been removed (such as `_model`-suffix on files in `models`-folder).

- The cursor is now a pointer when hovering over dropwdown menus.

- The table of match reports are no longer visible behind the round corners of the header when scrolling.

- The sort key for mail objects have been improved. Further improvements are on the way.

### Bugfixes

- The login-page in the report module now displays the correct error message on wrong username or password.

- After handling a match in the report module, the dropdown menus and checkboxes now work correctly.

- Non-superusers in the admin module can now access the error log.

- Deleting a ScanStatus object with a primary key larger than 1000 now works.

- Trying to log in as a user with duplicate aliases associated no longer fails.

- Trying to delete a missing object in the report module no longer creates one instead.

## Version 3.15.3, 13th July 2022

"Can't Reach It, Don't Need It"

### New in this version

- More reactive features in the user interface:

  - The report module no longer needs to refresh when a match is handled --
    matches are removed and updated dynamically.

  - The state of an organisational import task is now updated dynamically.

  - The scanner status page now has dynamic progress bars.

- Initial support for skipping objects:

  - Rules can be specified for dropping objects from the scan based on their
    path. (This functionality is off by default.)

- Support for running test scans:

  - Superusers can now specify that the matches produced by a scan should not
    be sent directly out to users.

  - These matches can either be handled by the superuser or be distributed to
    the recipients without scanning again.

- Matches in Microsoft Graph mail messages now include the name of the folder
  containing the mail.

### General Improvements

- HTTP throttling and backoff requests are now treated consistently across all
  data sources.

- The bottom of the report module's match view now shows the range of matches
  shown instead of a contextless page number.

- The side menus of both the admin and report modules are now fixed to the side
  of the screen.

- The "copy" button has been removed from matches from Microsoft Graph-based
  scans.

- A benchmarking framework has been implemented for future performance tests.

- The administration system's log viewer now supports paginated display.

### Bugfixes

- HTTP 503 Service Unavailable responses are now treated as backoff requests.

- The scanner engine's internal operations are now also constrained by a
  timeout, making the system much more able to continue after an unexpected
  failure.

- Nonconformant OpenDocument office files can now be detected and scanned
  correctly.

## Version 3.15.2, 23rd June 2022

"Natural Reactor"

### New in this version

- The scanner status page now automatically refreshes to track the status of
  running scans.

- Organizational structure is now displayed on the organizations page.

- Security improvements:

  - The user must now reenter or update the password used for authentication
    if the URL or the username of a scanner job is changed.
  
  - The database encryption key can now be easily rotated with the new
    `rotate_keys` command.

### Bugfixes

- A randomized timeout is now added to backoff requests from web APIs, reducing
  the risk of workers locking each other out of the server.

- Embedded objects now produce a correct `LastModified` date.

- All components of the scanner engine gracefully disconnect when the RabbitMQ
  message bus is stopped or restarted.

- Email elements whose name uses the MIME encoded-word syntax are now displayed
  correctly throughout the system.

## Version 3.15.1, 13th June 2022

"Gentlemen, we can rebuild him. We have the technology."

### General Improvements

- The e2_last_modified-attribute of a scanner is no longer set unless the
scan successfully finishes.

### Bugfixes

- The last_modified-property of a spawned object is no longer set to the time
it was spawned, but rather to the value of its parent object.

## Version 3.15.0, 3rd June 2022

"Hey! Listen!"

### New in this version

- Synchronisation of organisational information:

  - Organisational information imported from external systems is now available
    in both the administration system and the report module.

  - As a consequence, users who have not yet logged into the report module are
    still known to it, and can have matches associated with them.

- When a scanner job is completed, the associated administrative user will now
  receive an email summarising the data that was scanned.

- Error messages raised during the execution of a scan are now collected and
  displayed in the administration system.

### General improvements

- The location information shown for matches in the report module has been
  improved and made more consistent.

- The administration system no longer decrypts protected values for the sake of
  prepopulating a form.

- The user interface for Microsoft Graph scanner jobs now correctly shows the
  previously chosen organisational units, if there were any.

- Email attachments whose name includes non-ASCII characters are now correctly
  displayed.

### Bugfixes

- The system no longer appears to freeze when asked to scan a data source with
  no content.

- Network drive files whose name contains an invalid character no longer cause
  some of their siblings to be skipped.

- Scanning a Microsoft Graph organisational unit with no members no longer
  causes the whole organisation to be scanned.

- Microsoft Graph organisations with more than a single page of users are now
  supported correctly.

- The administration system's collector process can once more be run in
  parallel without risk of making the scan status inconsistent.

- The scanner motor can now correctly detect the deletion of Microsoft Graph
  mails.

- The administration system's collector process no longer raises a database
  error when it attempts to store an unexpectedly large object.

### Notes

- The logic that checks whether or not a file has changed since the last scan
  may reach the wrong conclusion for certain deeply-nested files. We expect a
  fix for this issue to be included in the next minor release.

## Version 3.14.3, 6th May 2022

"A Thousand Pictures Are Worth A Million Words"

### New in this version

- Scan status snapshots:

  - The system now records snapshots of the execution status of each scan.
  
  - This information will be used in future releases to improve scan time
    estimates and to provide a visualisation of the system's performance.

### General improvements

- The drive letters associated with network drives can now be used to specify
  an arbitrary path prefix.

- Database conflicts that may occur during the organisation creation process no
  longer produce an unhelpful default error page.

### Bugfixes

- The timestamps associated with scan status objects are once more kept up to
  date.

- Handled matches should no longer reappear when certain files are deleted.

- Microsoft Azure Active Directory accounts that do not define a first name or
  surname no longer cause import failures.

- The administration system no longer records changes to potentially sensitive
  scanner fields in the log.

- Organisations whose name contains a Danish character are now supported
  correctly.

## Version 3.14.2, 22nd April 2022
"Graphiti"

### New in this version

- Initial support for scanning Outlook Calendar appointments using Microsoft
  Graph.

- Support for importing organisational structure from Microsoft Azure Active
  Directory, as an alternative to on-premise AD synchronisation via LDAP.

- Initial support for selecting organizational units in Microsoft Graph-based
  scanners.

- The administration module documentation now includes an Office 365 section.

### General improvements

- Microsoft Graph-based scans of Office 365, OneDrive and SharePoint should now
  be considered mature enough for test deployments.

- OS2datascanner can now scan all tabs of a large spreadsheet file thanks to a
  new version of LibreOffice.

- Integrated support for profiling running code using Python's `cProfile`
  module.

- The "change password" forms are now accessible from the user interface.
  (This is primarily useful when not using an SSO based login.)

- The background job runner can now also run other tasks, not just LDAP import.

- Updated CD flow to our test servers.

### Bugfixes

- Email notifications now correctly display all results by default.

- Censored checkup objects no longer confuse the report module into hiding
  matches.

- Scan status objects now work reliably with Microsoft Graph-based scanners.

## Version 3.14.1, 15th March 2022
"Jet Fuel for the Parallelisation Rocket"

### New in this version

- The database indexes have been optimised for the administration system's
  collector process, allowing for better performance and more efficient
  parallelism.

- The log level of the background job runner can now be adjusted, enabling LDAP
  debugging.

### Bugfixes

- Changing the credentials of a data source no longer renders existing
  ScheduledCheckup messages invalid.

- The administration system's collector process now reminds restarted pipeline
  components that a scan has been cancelled.

- It is no longer possible to start multiple scans at once by clicking the
  "Let's go!" button several times in quick succession.

- When copying a file scanner, the "Skip super hidden" field is now included.

## Version 3.14.0, 1st March 2022

"A Parallel Universe"

### New in this version

- The pipeline collector processes are now parallelizable, allowing for multiple to be run whilst
keeping the database integrity intact. Thus, enabling scalability to enhance performance on large queues.

### Bugfixes

- Encountering filenames that used Windows 1252 characters previously raised a MemoryError which could lead
to scan stoppage. This is now caught.

- Email reports sent to users did not count matches younger than 30 days. These are now included
to reflect the default behaviour of the report module.

## Version 3.13.9, 17th February 2022

"The Hits Keep Coming"

New in this version:

- The pipeline collector processes now also report Prometheus metrics, enabling
  better monitoring.

General improvements:

- To more extensively test the functionality and performance of the scanner
  engine, the test suite now includes simulated scans of a suite of
  randomly-generated websites.

Bugfixes:

- Embedded containers, such as Zip files or MIME-format messages, are no longer
  misreported as separate top-level sources.

- A scan that includes an invalid source, such as an Exchange scan that
  requests a nonexistent account, will no longer appear to be stuck.

## Version 3.13.8, 11th February 2022

"The Long Walk"

Bugfixes:

- The name and address rules now behave correctly again.

- Errors produced during the rule matching process are once more correctly
  transmitted to the report module.

- Additional safety preconditions are now performed before checking SMB file
  attributes.

## Version 3.13.7, 10th February 2022

"Brown Paper Bag"

This minor release improves some of the project's internal documentation and
fixes a bug in a recently-introduced migration.

## Version 3.13.6, 9th February 2022

"Postel's Principle"

### General improvements

- The OS2datascanner version number is now also included in the scanner
  engine's HTTP `User-Agent` field.

- The scanner engine should now do a better job of throttling its web scan
  functions.

### Bugfixes

- All CSV files, including those generated internally when converting certain
  spreadsheets, are now scanned correctly.

- The detection code for live backup folders on network shares is now more
  tolerant of metadata inconsistencies.

## Version 3.13.5, 27th January 2022

"Back Down, Speed Up"

### New in this version

- Initial support for Microsoft Graph backoff messages.

- Initial support for retrieving metadata from OneDrive and SharePoint files.

- Support for converting URLs to scan sources using the API server.

### General improvements

- Matches in the report module are now presented in a more predictable and
  consistent order.

- Exchange Web Services scans now use OS2datascanner's common backoff services
  rather than the unusual `exchangelib` implementation.

- JBIG2 and CCITT Group 4 images embedded in PDF files are now correctly
  extracted and scanned.

- Microsoft Graph accounts are no longer scanned as single objects, allowing
  for greater parallelisation.

- Emails discovered under exploration of a Microsoft Graph account are now sent
  to the pipeline as soon as they're discovered.

- Better support for benchmarking the performance of sources.

### Bugfixes

- Connections to Microsoft Graph API services are now reused for future calls
  rather than being torn down immediately.

- The administration system's pipeline collector will no longer stop if it
  receives a message whose content is rejected by the database.

- The report module's pipeline collector now applies more corrective
  transformations to messages whose content is rejected by the database.

## Version 3.13.4, 5th January 2022

"Authorless"

### General improvements

- The user interface now uses version 3.2.11 of the Django framework.

### Bugfixes

- Better support for extracting pdf metadata without any author. 

## Version 3.13.3, 22nd December 2021

"Soft gifts"

### General improvements

- The admin module now has a command for creating a new web source on demand.

### Bugfixes

- Select option dropdowns are now accessible from the keyboard.

- The report module data migrations now supports old data formats.

- Automatic reload works again in development when files are changed. 

## Version 3.13.2, 7th December 2021

"Erase & rewind" 

### New in this version
- Experimental support for cancelling a scan:

  - Deleting the status object for a running scan will now signal to the
    pipeline that it should ignore the tasks from that scan.

### General improvements

- The sort keys used by the report module's database can now be recomputed.

- Custom pagination values are now preserved when filter options are changed.

- Style and presentation resources are now shared between the administration
  system and report module for greater consistency.

- The errors produced when an invalid TOML configuration file is detected are
  now more informative.

### Bugfixes

- Scanning stream-compressed files should now work properly again.

- The progress of an LDAP synchronisation background job is once again
  correctly reported to the administration system.

- The test suite of the administration system can now be run in the development
  environment without causing conflicts with the report module.

- Errors late in a scan should no longer cause status objects to get out of
  sync.

- The rule engine can once again request new conversions from the scan pipeline
  without producing incoherent results.

- Improved handling of PostgreSQL database limitations:

  - The report module's pipeline collector now strips all instances of the null
    byte (Unicode character U+0000) from JSON objects before saving them to the
    database.

### Notes

- The repository now contains (Danish-language) documentation for the process
  of setting up an OS2datascanner installation for use with Microsoft Graph.

- Due to the nature of the conversion bug in the rule engine, it is recommended
  that scans performed with releases `3.13.0` or `3.13.1` be repeated.

## Version 3.13.1, 16th November 2021

"Batch Processing" 

### New in this version

- Support for protocol-level pagination for Microsoft Graph emails.

- Support for automatic renewal of Microsoft Graph access token.

### General improvements

- The proactive restart logic now uses `sys.exit` to terminate the Docker
  container.

- The report module's performance has been improved by making better use of
  database indexes.

### Bugfixes

- Previously selected organisational units are now correctly shown when editing
  an existing scanner job.

- The report module can once more handle messages for objects with unusually
  long names.

## Version 3.13.0, 4th November 2021

"An Iron Fist in a Velvet Glove"

### New in this version

- Support for new types of rules:

  - The name and address rules from the OS2datascanner 2.x series are once more
    available in the administration system.

  - The administration system now also includes a new rule for Danish-language
    medical terminology. (This rule uses a mechanically-generated data set and
    so may produce false positives.)

- A refreshed user interface:

  - A new user interface has been introduced in the report module.

  - The design of both the administration system and the report module has been
    made responsive.

### General improvements

- Improved the reliability of the scanner engine:

  - Pipeline components can now proactively restart themselves to defend
    against potential resource leaks in third-party libraries.

  - Messages sent between pipeline components are now compressed to reduce
    network traffic.

  - Messages sent between pipeline components are now stored more reliably on
    the disk.

- The project's JavaScript and Python code is now subject to automated quality
  and consistency checks.

- Matches should now be presented in the report module in a more intuitive
  order.

- The web scanner now produces more helpful information when it encounters a
  dead link.

- The report module's database queries now have better performance.

- The documentation now includes remarks about how to run test scans for a
  selection of data sources.

- The development environment now incorporates MailHog, to make it easier to
  test email-related functionality.

### Bugfixes

- Errors produced during the rule matching process no longer cause
  pipeline components to fail.

- The web scanner no longer follows `nofollow` links and so should be able to
  traverse procedurally-generated web pages more safely.

- Scanners no longer declare that they are still running in the event that
  extra checks have caused more objects to be scanned than were initially
  found.

- Microsoft Graph and web aliases are now correctly translated to database
  relations in the report module.

- Sending mail notifications now uses significantly fewer system resources.

- Deleting a scanner job that is executing no longer causes the administration
  system's status overview to get out of sync.

- Temporary files created by external tools are now correctly deleted when the
  tools are forcibly stopped.

- RabbitMQ should no longer conclude that a pipeline component executing a
  complex task is unresponsive and should be disconnected.

## Version 3.12.1, 11th October 2021

This minor bugfix release restores backwards compatibility with messages from
older versions of OS2datascanner.

## Version 3.12.0, 5th October 2021

"Stay In Your Lane"

### General improvements

- The pipeline's worker processes can now be locked to a specific CPU, allowing
  them to work more effectively without interfering with each other.

- The administration system and report module now maintain a more detailed log
  of the actions taken by the user.

### Bugfixes

- Organisational updates in the administration system are once more reflected
  to the report module.

- The regular expression rule form no longer produces strange failures when
  field values are incorrect or incomplete.

- CPR numbers that identify dates for which checksum digits are optional are
  now handled correctly.

## Version 3.11.7, 4th October 2021

"To kill a Mockingbird"

### New in this version

- The Webscanner is now agnostic about a set of common subdomains:

  - When specifying the url of a site, it is no longer important to specify
    e.g. a `www` subdomain. The list of common subdomains that are treated as
    equal are `"www", "www2", "m", "ww1", "ww2", "en", "da", "secure"`

- Support for canceling a scan:

  - The queue system was recently changed to be persistent, meaning that no
    messages were lost if OS2datascanner was updated or restarted. As a
    side-effect it was impossible to cancel a running scan. This release makes
    it possible again to stop a running scan.
    Note: This is *initial* support and not hooked up to the user interface
    yet.

### General improvements

- The `CPRRule` is updated with a list prefix-words that indicates a false
  match:

  - The list of prefixes is updated using feedback from users. If any of the
    `prefix` words are found in the content and there is a match, the `CPRRule`
    discard the match as false positive.
    The list of prefixes are found in `src/os2datascanner/engine2/rules/cpr.py`

- Metrics are now collected from the admin- and report Django applications:

  - The metrics are sent to prometheus and includes `requests latency`,
    `number of requests` and related performance numbers. No user specific
    information is collected.
    The collected metrics can be seen with on port `5001` from within the
    container, e.g. `docker-compose exec report bash -c "curl localhost:5001"`

- There is now a timout value for downloading sitemaps. You server doens't
  respond? No problem, OS2datascanner now have a default timout of 45s for all
  http-related requests. This can be changed in the `engine`s toml
  configuration. See `src/os2datascanner/engine2/default-settings.toml` for
  default values.

### Bugfixes

- `scanenr_info`, one of the new administration helper commands, had a memory
  issue for very large scans. This have been fixed and it is possible to get
  info about VLS (very large scans).

## Version 3.11.6, 30th September 2021

"New Double-Action Formula!"

### New in this version

- Support for prefetching messages:

  - Pipeline components can now collect future tasks from the server while they
    execute other tasks, greatly reducing protocol overhead and improving
    performance.

  - (Although message prefetching was disabled in version 3.3.1 to improve
    reliability, the background thread introduced in the previous version makes
    it possible to take advantage of this feature safely.)

- Support for directly opening file folders:

  - The report module can now give direct links to the network drive folders in
    which files with matches have been found, when the administrator has
    configured the network to allow this.

- The report module now has a management command for extracting information
  about running scans.

### General improvements

- Multiple organisational units can now be chosen from across the organisation
  when setting up an Exchange scanner job.

- By default, the report module now displays matches from the last 30 days
  instead of concealing them.

- The administration system and report module now have helper commands for
  setting up a useful development environment.

- The documentation now includes an outline of the test LDAP server.

- Scanner status objects in the database are now automatically timestamped
  whenever they are updated.

- The underlying web frameworks now support WebSockets and ASGI, which future
  releases will use to provide live updates to the browser.

- To work around servers that do not correctly send the HTTP 405 response to an
  unsupported request method, the integrated web crawler now uses GET requests
  when checking external links.

- Less logging output is now produced by default.

### Bugfixes

- The web scanner no longer misdetects `mailto:` and `tel:` URLs as broken
  links.

- The Danish translation of the user interface now correctly and consistently
  uses the imperative form of certain verbs.

- Links to the low-level administration pages are now only shown to superusers.

- SSO users without a defined email address no longer produce errors in the
  report module's metadata handling code.

### Notes

- When a web scan based on a sitemap file is requested, OS2datascanner will now
  only visit the links given in the file and will not otherwise crawl the site.

- The target Python version for all parts of the OS2datascanner system is now
  **3.9**.

## Version 3.11.5, 15th September 2021

"We Tried To Deliver Your Package, But You Were Out"

### New in this version

- The scanner engine now supports rolling updates during scans:

  - RabbitMQ communications are now managed by a background thread, improving
    connection reliability during long operations.

  - Scans can now be stopped and started again without losing any messages.

- A management command summarising the results of a scanner job has been added.

### General improvements

- The administration system's scanner status page now has a cleaner and more
  reliable presentation. 

## Version 3.11.4, 9th September 2021

This hotfix release corrects webscan link parsing.

## Version 3.11.3, 7th September 2021

"Identical Twins"

### New in this version

- Support for copying scanner jobs:

  - An existing scanner job can now be used as a template to create a new one.

### General improvements

- Better logging of exceptions in the pipeline.

- Scan status information objects are now paginated.

- LDAP synchronisation is now automatically performed once a day.

- Improved the DPO and manager overviews:

  - DPOs can now see which months have the most unhandled matches.

  - Managers can now see which users have the most unhandled matches.

- The administration system now contains a link to the corresponding report
  module.

- Various legacy database entries and their associated fields in the UI have
  been removed.

- Required fields in the administration system are now consistently marked with
  asterisks.

### Bugfixes

- The validation status of a scanner job is now always enforced, also for
  system administrators.

- A scanner job's validation status can now be consistently edited.

- Different scanner types now have different icons in the report module.

- It is no longer necessary to re-select the organisation when editing a
  scanner job.

- LDAP synchronisation no longer fails when Keycloak omits a required field
  whose value would otherwise be empty.

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
