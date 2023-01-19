# Data sources

OS2datascanner supports many data sources, and only a thin API layer is needed
to connect more to the system. This document gives a brief overview of them.

## Dropbox

## Exchange Web Services

OS2datascanner can connect to a Microsoft Exchange installation, either locally
or in the cloud, using the
[Exchange Web Services](https://docs.microsoft.com/en-us/exchange/client-developer/exchange-web-services/explore-the-ews-managed-api-ews-and-web-services-in-exchange)
API. (OS2datascanner uses the [`exchangelib`])(https://github.com/ecederstrand/exchangelib)
package as its implementation of the API.)

### Try it out

(To the best of the project's knowledge, there exist no independent
implementations of the Exchange Web Services API, so you'll need access to a
functioning Exchange installation to follow these steps.)

Under the _Exchangescanner_ tab in the administration system, choose _Add
scannerjob_.

In the _URL_ field, provide the domain whose emails should be scanned, with or
without a leading `@` sign (for example, `@company.example`).

In the _Service endpoint_ field, provide the URL to the Exchange Web Services
API instance. If you don't fill it in, then the EWS autodiscovery protocol will
be used instead.

Under _Brugernavn_ og _Adgangskode_, you'll need to provide the details of a
service account with the special role `ApplicationImpersonation`. Having this
role lets a service account act on behalf of any other user in the same
management scope. (Naturally, OS2datascanner only uses this to read messages.)
Contact your system administrator if you don't have access to such an account.

(Note that _Brugernavn_ should typically resemble an email address -- that is,
`service-account@company.example`, not `service-account`.)

> Note that Exchange Web Services for Office 365 does not support this use of a
> service account as of December 31st, 2022. This means that EWS can only
> presently be used to communicate with on-premises installations.

EWS doesn't offer any way of discovering the users present in an Exchange
installation, so you'll need to get that from Active Directory or from Azure
AD. Choose the _Organisatoriske enheder_ field to use OS2datascanner's LDAP
support to automatically scan all of the users detected in your organisational
hierarchy, or upload a UTF-8 text file with one account name on each line with
_Upload fil_.

[comment:] # ## Filesystem scans

## Google Workspace

OS2datascanner has initial support for scanning organisational Gmail and Google
Drive accounts. Google Workspace does not support the OAuth2 client credentials
flow used by the Microsoft Graph sources, so the use of these data sources
requires a lot of manual configuration.

## HTTP

OS2datascanner can scan web sites in two ways:

* as a traditional crawler, that traverses all of the links and references
  found in a web site and scans these recursively; or

* as a simple linear scan of all of the resources enumerated in a [sitemap XML
  file](https://www.sitemaps.org/protocol.html) (either one present on the site
  or one uploaded to the administration system).

As a policy decision, OS2datascanner does not honour the `robots.txt` file, so
you should normally only run it on sites under your control.

Note that OS2datascanner's user agent advertises both its own version and that
of the underlying `python-requests` library:

    OS2datascanner 3.17.7 (python-requests/2.28.1) (+https://os2datascanner.dk/agent)

Be aware of this if you need to whitelist the user agent; in particular, make
sure that a blacklist rule for `python-requests` doesn't take priority.

### Try it out

The development environment includes a web server with a few conspicuous files.
Under the _Webscanner tab in the administration system, choose _Add
scannerjob_, and specify the URL `http://nginx/`.

The web server can be scanned both with a sitemap (`http://nginx/sitemap.xml`)
and without.

## Microsoft Graph

OS2datascanner has support for scanning resources present in Microsoft Graph,
and can participate in the normal OAuth2 client credentials flow to allow
administrators to revocably delegate permissions to an OS2datascanner instance.
Microsoft Graph can also be used as a source of organisational information.

Office 365 mails, OneDrive and SharePoint files, and calendar invitations are
the only resources presently supported. ([Microsoft restricts API access to
Microsoft Teams](https://learn.microsoft.com/da-dk/graph/teams-protected-apis),
so this feature remains under internal test.)

### Try it out

Log in to your Microsoft Graph tenant as a global administrator. Under the
_App registrations_ blade, choose _New registration_.

Choose a name for the application (_OS2datascanner dev test_, for example),
specify that it's a single tenant app, and give
`http://localhost:8040/grants/msgraph/receive/` as a redirect URL (of type
_Web_).

Under the resulting _Overview_ blade, copy the application ID and provide it to
the OS2datascanner administration system as the setting `MSGRAPH_APP_ID`. Then
open the _Certificates & secrets_ blade and create a new client secret. Copy
its value and provide it to the administration system as the setting
`MSGRAPH_CLIENT_SECRET`.

Open the _API permissions_ blade and give the application the following
_application permissions_:

* `Calendars.Read`
* `Directory.Read.All`
* `Files.Read.All`
* `Mail.Read`
* `Sites.Read.All`

(Because OS2datascanner doesn't operate in the context of a specific user, but
rather of the organisation as a whole, these must be application permissions
rather than delegated ones.)

Once you've done that, return to your OS2datascanner instance and choose one
of the _Office 365_ scanner types. The first time you set one of these up,
you'll be redirected to Microsoft and asked to confirm that you want your
OS2datascanner instance to have access to your tenant; after this has been done
once, OS2datascanner will remember the delegation and reuse it for future
scanner jobs.

## SMB

Using the `libsmbclient` and `pysmbc` packages, OS2datascanner can scan SMB
servers, better known as Windows network drives. These packages also give
OS2datascanner the ability to perform ad hoc authentication using normal
Windows login credentials, so there's no need to permanently enroll the scanner
engine's server into the Windows domain.

(OS2datascanner can also use the SMB support built into the operating system
kernel, but this is deprecated, as it requires that certain scanner components
be given higher privilege levels.)

### Try it out

The development environment includes a Samba server which you can use to test
SMB scans. Under the _Filescanner_ tab in the administration system, choose
_Add scannerjob_.

The _URL_ field is used to specify the UNC path to the network drive you'd like
to scan. UNC paths are of the form `//server-name/path/to/folder` (with either
forward or backward slashes). Fill in `//samba/e2test` here.

(If your Windows environment maps the given UNC path to a drive letter, you can
optionally provide that in the _Drevbogstav_ field. This is only used for
display purposes.)

Under the _Brugeroplysninger_ section, leave the _Brugerdomæne_ field empty,
and specify the username `os2` and the password `swordfish`.
