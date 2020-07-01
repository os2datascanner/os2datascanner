DEBUG = True

SITE_ID = 1

ALLOWED_HOSTS = []

# Site URL for calculating absolute URLs in emails.
SITE_URL = 'INSERT_DOMAIN_NAME'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'DUMMYKEY(for development)DUMMYKEY(for development)'

# Used for filescan and mounting
PRODUCTION_MODE = False

# If webscan on the current installation is needed, enable it here
ENABLE_WEBSCAN = True

# If filescan on the current installation is needed, enable it here
ENABLE_FILESCAN = True

# If exchangescan on the current installation is needed, enable it here
ENABLE_EXCHANGESCAN = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'os2datascanner_admin',
        'USER': 'os2datascanner_admin_dev',
        'PASSWORD': 'os2datascanner_admin_dev',
        'HOST': 'db',
    }
}

DATABASE_POOL_ARGS = {
    'max_overflow': 10,
    'pool_size': 5,
    'recycle': 300
}

# Email settings
DEFAULT_FROM_EMAIL = 'os2datascanner@INSERT_DOMAIN_NAME'
ADMIN_EMAIL = 'os2datascanner@INSERT_DOMAIN_NAME'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'