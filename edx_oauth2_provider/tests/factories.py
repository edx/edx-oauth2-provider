from django.contrib.auth.models import User

import factory
from factory.django import DjangoModelFactory

import provider.oauth2.models
from provider.constants import CONFIDENTIAL

from .. import models


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username', )

    username = factory.Sequence(u'robot_{0}'.format)
    email = factory.Sequence(u'robot_{0}@edx.org'.format)
    password = factory.PostGenerationMethodCall('set_password', 'some_password')

    first_name = factory.Sequence(u'Robot{0}'.format)
    last_name = 'Test'

    is_staff = False
    is_active = True
    is_superuser = False


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = provider.oauth2.models.Client

    client_id = factory.Sequence(u'client_{0}'.format)
    client_secret = 'some_secret'
    client_type = CONFIDENTIAL

    url = 'http://example.com'
    redirect_uri = 'http://example.com/application'


class TrustedClientFactory(DjangoModelFactory):
    class Meta:
        model = models.TrustedClient


class AccessTokenFactory(DjangoModelFactory):
    class Meta:
        model = provider.oauth2.models.AccessToken
        django_get_or_create = ('user', 'client')
