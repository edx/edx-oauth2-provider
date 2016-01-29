"""
Django settings for example project.
"""
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Tester', 'test@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '%s/db.sqlite' % os.path.dirname(__file__),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}


SITE_ID = 1

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret'

ROOT_URLCONF = 'tests.urls'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/login/'

TEMPLATE_DIRS = ('tests',)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'edx_oauth2_provider',
    'provider',
    'provider.oauth2',
)

OAUTH_OIDC_ISSUER = 'https://example.com/oauth2'

OAUTH_OIDC_ID_TOKEN_HANDLERS = (
    'edx_oauth2_provider.oidc.handlers.BasicIDTokenHandler',
    'edx_oauth2_provider.oidc.handlers.ProfileHandler',
    'edx_oauth2_provider.oidc.handlers.EmailHandler',
    'edx_oauth2_provider.tests.handlers.TestHandler'
)

OAUTH_OIDC_USERINFO_HANDLERS = (
    'edx_oauth2_provider.oidc.handlers.BasicUserInfoHandler',
    'edx_oauth2_provider.oidc.handlers.ProfileHandler',
    'edx_oauth2_provider.oidc.handlers.EmailHandler',
    'edx_oauth2_provider.tests.handlers.TestHandler'
)
