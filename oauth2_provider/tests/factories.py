from django.contrib.auth.models import User

from factory.django import DjangoModelFactory

from factory import PostGenerationMethodCall

import provider.oauth2.models
import oauth2_provider.models

CLIENT_URL = 'http://example.com'
CLIENT_REDIRECT_URI = 'http://example.com/application'


class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User
    password = PostGenerationMethodCall('set_password', 'test')


class ClientFactory(DjangoModelFactory):
    FACTORY_FOR = provider.oauth2.models.Client

    url = CLIENT_URL
    redirect_uri = CLIENT_REDIRECT_URI


class TrustedClientFactory(DjangoModelFactory):
    FACTORY_FOR = oauth2_provider.models.TrustedClient
