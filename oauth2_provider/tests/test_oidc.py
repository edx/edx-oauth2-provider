# pylint: disable=missing-docstring

import datetime
import uuid

from django.conf import settings
from django.test.utils import override_settings

import mock

from provider.scope import check

from oauth2_provider import constants
from oauth2_provider.oidc import make_id_token, encode_id_token
from oauth2_provider.tests.base import BaseTestCase

BASE_DATETIME = datetime.datetime(1970, 1, 1)


@mock.patch('django.utils.timezone.now', mock.Mock(return_value=BASE_DATETIME))
@override_settings(OAUTH_OIDC_ISSUER='https://example.com/')
class IdTokenTest(BaseTestCase):
    def setUp(self):
        super(IdTokenTest, self).setUp()
        self.nonce = unicode(uuid.uuid4())

    def _get_actual_id_token(self, access_token, nonce):
        with mock.patch('oauth2_provider.oidc.handlers.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = BASE_DATETIME
            id_token = make_id_token(access_token, nonce)
            return id_token

    def _get_expected_id_token(self, access_token, nonce):
        client = access_token.client

        # Basic OpenID Connect ID token claims
        expected = {
            'iss': settings.OAUTH_OIDC_ISSUER,
            'sub': access_token.user.username,
            'aud': client.client_id,
            'iat': 0,
            'exp': 30,
            'nonce': nonce
        }

        # Add profile scope claims
        if check(constants.PROFILE_SCOPE, access_token.scope):
            user = access_token.user
            expected.update({
                'name': user.get_full_name(),
                'given_name': user.first_name,
                'family_name': user.last_name,
                'preferred_username': user.username
            })

        # Add email scope claims
        if check(constants.EMAIL_SCOPE, access_token.scope):
            user = access_token.user
            expected.update({
                'email': user.email,
            })

        return expected

    def _encode_id_token(self, token, secret):
        # Sort using keys to avoid errors in comparison. Equivalent
        # dictionaries will get different JSON strings if the order of
        # the keys in their internal representation is different.
        token = dict([(k, token[k]) for k in sorted(token.keys())])

        return encode_id_token(token, secret)

    def test_get_id_token(self):
        actual = self._get_actual_id_token(self.access_token, self.nonce)
        expected = self._get_expected_id_token(self.access_token, self.nonce)
        self.assertEqual(actual, expected)

        self.assertEqual(self._encode_id_token(actual, 'test_secret'),
                         self._encode_id_token(expected, 'test_secret'))

    def test_get_id_token_with_profile(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE
        self.access_token.save()

        actual = self._get_actual_id_token(self.access_token, self.nonce)
        expected = self._get_expected_id_token(self.access_token, self.nonce)
        self.assertEqual(actual, expected)

    def test_get_id_token_with_profile_and_email(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE | constants.EMAIL_SCOPE
        self.access_token.save()

        actual = self._get_actual_id_token(self.access_token, self.nonce)
        expected = self._get_expected_id_token(self.access_token, self.nonce)
        self.assertEqual(actual, expected)
