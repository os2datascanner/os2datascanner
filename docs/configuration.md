The OS2Datascanner system is configured using `.toml`-files - one for each
module. Most configuration settings come with reasonable defaults and need not
be changed for a standard set-up, but most can be adjusted as needed, and a few
must be given in order for the system to work. Below follows minimal examples
for each module.


## Configuration for the Admin-module

An almost minimal example of the `admin-user-settings.toml` configuration file:

```toml
SECRET_KEY = "<some secret key - see Django documentation>"
DECRYPTION_HEX = "<hex value of 32 random bytes for en-/decryption>"

# [site]
# The URL of this site, used in links in emails and in the redirect URL for
# OAuth 2.0 services. (This value should end with a forward slash.)
SITE_URL = "<domain url for admin module>"
# See the official Django documentation for details on ALLOWED_HOSTS
ALLOWED_HOSTS = []

# [scans] All scans are disabled by default, enable only the ones to use
ENABLE_FILESCAN = true
ENABLE_WEBSCAN = true
ENABLE_EXCHANGESCAN = true

# [email]
DEFAULT_FROM_EMAIL = "<email address used as sender from the system>"
ADMIN_EMAIL = "<email address for sys-admin>"
EMAIL_HOST = "<host name of email service>"

[amqp]
# Nested amqp settings are picked up by the common amqp utility module
AMQP_HOST = "<amqp service name>"
AMQP_USER = "<amqp user name>"
AMQP_PWD = "<amqp user password>"

[DATABASES]

    [DATABASES.default]
    ENGINE = "django.db.backends.postgresql_psycopg2"
    NAME = "os2datascanner_admin"
    USER = "<user name for dedicated admin db-user>"
    PASSWORD = "<user password for dedicated admin db-user>"
    HOST = "<database service name>"
```


## Configuration for the Engine components

A minimal example of the `enginge-user-settings.toml` configuration file:

```toml
[amqp]
# Nested amqp settings are picked up by the common amqp utility module
AMQP_HOST = "<amqp service name>"
AMQP_USER = "<amqp user name>"
AMQP_PWD = "<amqp user password>"
```


## Configuration for the Report-module

An almost minimal example of the `report-user-settings.toml` configuration file
can be seen below. **Please note:** the metadata settings for `SAML2_AUTH` are
mutually exclusive, and you should only ever set one of them.

```toml
SECRET_KEY = "<some secret key - see Django documentation>"

# [site]
# The URL of this site, used in links in emails and in the redirect URL for
# OAuth 2.0 services. (This value should end with a forward slash.)
SITE_URL = "<domain url for admin module>"
# See the official Django documentation for details on ALLOWED_HOSTS
ALLOWED_HOSTS = []

# [installation]
# The name of the institution, to be included in the notification signoff
NOTIFICATION_INSTITUTION = '<organisation name>'

# [email]
DEFAULT_FROM_EMAIL = "<email address used as sender from the system>"
ADMIN_EMAIL = "<email address for sys-admin>"
EMAIL_HOST = "<host name of email service>"

[amqp]
# Nested amqp settings are picked up by the common amqp utility module
AMQP_HOST = "<amqp service name>"
AMQP_USER = "<amqp user name>"
AMQP_PWD = "<amqp user password>"

[DATABASES]

    [DATABASES.default]
    ENGINE = "django.db.backends.postgresql_psycopg2"
    NAME = "os2datascanner_admin"
    USER = "<user name for dedicated admin db-user>"
    PASSWORD = "<user password for dedicated admin db-user>"
    HOST = "<database service name>"

# The full documentation can be found here: https://github.com/fangli/django-saml2-auth
[SAML2_AUTH]

# Metadata is required
# NB!!  Choose EITHER remote url or local file path
METADATA_AUTO_CONF_URL = '[The auto(dynamic) metadata configuration URL of SAML2]'
METADATA_LOCAL_FILE_PATH = '[The metadata configuration file path]'
```
