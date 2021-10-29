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
API instance. This field is optional; if you don't fill it in, then the EWS
autodiscovery protocol will be used. To scan an Office 365 installation, use
the common URL `https://outlook.office365.com/EWS/Exchange.asmx`.

Under _Brugernavn_ og _Adgangskode_, you'll need to provide the details of a
service account with the special role `ApplicationImpersonation`. Having this
role lets a service account act on behalf of any other user in the same
management scope. (Naturally, OS2datascanner only uses this to read messages.)
Contact your system administrator if you don't have access to such an account.

(Note that _Brugernavn_ should typically resemble an email address -- that is,
`service-account@company.example`, not `service-account`.)

EWS doesn't offer any way of discovering the users present in an Exchange
installation, so you'll need to get that from Active Directory or from Azure
AD. Choose the _Organisatoriske enheder_ field to use OS2datascanner's LDAP
support to automatically scan all of the users detected in your organisational
hierarchy, or upload a UTF-8 text file with one account name on each line with
_Upload fil_.

## Filesystem scans

## Gmail

## Google Drive

## HTTP

## Microsoft Graph

## SMB

Using the `libsmbclient` and `pysmbc` packages, OS2datascanner can scan SMB
servers, better known as Windows network drives.

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
