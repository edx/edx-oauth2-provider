"""
Django settings for example project.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os

DEBUG = True

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

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secret'

ROOT_URLCONF = 'tests.urls'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/login/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': ('django.contrib.auth.context_processors.auth',),
            'debug': DEBUG
        }
    }
]

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
    'edx_oauth2_provider.tests.handlers.DummyHandler'
)

OAUTH_OIDC_USERINFO_HANDLERS = (
    'edx_oauth2_provider.oidc.handlers.BasicUserInfoHandler',
    'edx_oauth2_provider.oidc.handlers.ProfileHandler',
    'edx_oauth2_provider.oidc.handlers.EmailHandler',
    'edx_oauth2_provider.tests.handlers.DummyHandler'
)
