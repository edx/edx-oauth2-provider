# pylint: disable=missing-docstring

from django.test import TestCase
from provider.oauth2.models import Client, AccessToken, RefreshToken

from .factories import (
    UserFactory,
    ClientFactory,
    AccessTokenFactory,
    RefreshTokenFactory
)


class TestFactory(TestCase):
    def setUp(self):
        super(TestFactory, self).setUp()

    def test_client_factory(self):
        user = UserFactory()
        actual_client = ClientFactory(user=user)
        expected_client = Client.objects.get(user=user)
        self.assertEqual(actual_client, expected_client)

    def test_access_token_client_factory(self):
        user = UserFactory()
        actual_access_token = AccessTokenFactory(user=user, client=ClientFactory())
        expected_access_token = AccessToken.objects.get(user=user)
        self.assertEqual(actual_access_token, expected_access_token)

    def test_refresh_token_factory(self):
        user = UserFactory()
        client = ClientFactory()
        access_token = AccessTokenFactory(user=user, client=client)
        actual_refresh_token = RefreshTokenFactory(user=user, client=client, access_token=access_token)
        expected_refresh_token = RefreshToken.objects.get(user=user, access_token=access_token)
        self.assertEqual(actual_refresh_token, expected_refresh_token)
