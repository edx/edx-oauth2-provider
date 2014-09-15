from django.contrib.auth.models import User

import factory
from factory.django import DjangoModelFactory

import provider.oauth2.models
from provider.constants import CONFIDENTIAL

import oauth2_provider.models


class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User
    FACTORY_DJANGO_GET_OR_CREATE = ('username', )

    username = factory.Sequence(u'robot_{0}'.format)
    email = factory.Sequence(u'robot_{0}@edx.org'.format)
    password = factory.PostGenerationMethodCall('set_password', 'some_password')

    first_name = factory.Sequence(u'Robot{0}'.format)
    last_name = 'Test'

    is_staff = False
    is_active = True
    is_superuser = False


class ClientFactory(DjangoModelFactory):
    FACTORY_FOR = provider.oauth2.models.Client

    client_id = factory.Sequence(u'client_{0}'.format)
    client_secret = 'some_secret'
    client_type = CONFIDENTIAL

    url = 'http://example.com'
    redirect_uri = 'http://example.com/application'


class TrustedClientFactory(DjangoModelFactory):
    FACTORY_FOR = oauth2_provider.models.TrustedClient


class AccessTokenFactory(DjangoModelFactory):
    FACTORY_FOR = provider.oauth2.models.AccessToken
    FACTORY_DJANGO_GET_OR_CREATE = ('user', 'client')
