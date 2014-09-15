# pylint: disable=missing-docstring

import datetime
import uuid

from django.conf import settings
from django.test.utils import override_settings

import mock

from provider.scope import check

from oauth2_provider import constants
from oauth2_provider.oidc import id_token_claims, encode_claims, userinfo_claims
from oauth2_provider.tests.base import BaseTestCase

BASE_DATETIME = datetime.datetime(1970, 1, 1)


@mock.patch('django.utils.timezone.now', mock.Mock(return_value=BASE_DATETIME))
@override_settings(OAUTH_OIDC_ISSUER='https://example.com/')
class OIDCTestCase(BaseTestCase):
    def setUp(self):
        super(OIDCTestCase, self).setUp()
        self.nonce = unicode(uuid.uuid4())


class IdTokenTest(OIDCTestCase):
    def _get_actual_id_token(self, access_token, nonce):
        with mock.patch('oauth2_provider.oidc.handlers.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = BASE_DATETIME
            id_token = id_token_claims(access_token, nonce)

            self.assertIn('sub', id_token)
            id_token['sub'] = None  # clear id token since a handler can change it
            return id_token

    def _get_expected_id_token(self, access_token, nonce):
        client = access_token.client

        # Basic OpenID Connect ID token claims
        expected = {
            'iss': settings.OAUTH_OIDC_ISSUER,
            'sub': None,
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

        return encode_claims(token, secret)

    def test_get_id_token(self):
        claims = self._get_actual_id_token(self.access_token, self.nonce)
        expected = self._get_expected_id_token(self.access_token, self.nonce)
        self.assertEqual(claims, expected)
        self.assertEqual(self._encode_id_token(claims, 'test_secret'),
                         self._encode_id_token(expected, 'test_secret'))

    def test_get_id_token_with_profile(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE
        self.access_token.save()

        claims = self._get_actual_id_token(self.access_token, self.nonce)
        expected = self._get_expected_id_token(self.access_token, self.nonce)
        self.assertEqual(claims, expected)

    def test_get_id_token_with_profile_and_email(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE | constants.EMAIL_SCOPE
        self.access_token.save()

        claims = self._get_actual_id_token(self.access_token, self.nonce)
        expected = self._get_expected_id_token(self.access_token, self.nonce)
        self.assertEqual(claims, expected)


class UserInfoTest(OIDCTestCase):
    def assertIncludedClaims(self, claims, expected_scope=None, expected_claims=None):
        expected_scope = expected_scope if expected_scope else []
        expected_claims = expected_claims if expected_claims else []

        # Should always have a subject claim
        expected_claims.extend(['sub'])

        for scope in expected_scope:
            if scope == 'profile':
                expected_claims.extend(['preferred_username',
                                        'given_name',
                                        'family_name',
                                        'name'])
            if scope == 'email':
                expected_claims.extend(['email'])

        self.assertItemsEqual(claims.keys(), expected_claims)

    def test_values(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE
        self.access_token.save()

        claims = userinfo_claims(self.access_token, claims_request={'preferred_username': {'value': 'pedro'}})

    def test_arguments(self):
        """ Test if the responses contain the requested claims according to permissions"""
        # TODO: repplace with DDT test

        def userinfo_req(req):
            return {'userinfo': req}

        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE
        self.access_token.save()

        claims = userinfo_claims(self.access_token)
        self.assertIncludedClaims(claims, ['profile'])

        claims = userinfo_claims(self.access_token, scope_names=['openid', 'profile', 'email'])
        self.assertIncludedClaims(claims, ['profile'])

        claims = userinfo_claims(self.access_token, scope_names=['openid', 'email'])
        self.assertIncludedClaims(claims)

        claims = userinfo_claims(
            self.access_token,
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, expected_claims=['preferred_username'])

        claims = userinfo_claims(self.access_token, scope_names=['email'])
        self.assertIncludedClaims(claims)

        claims = userinfo_claims(
            self.access_token,
            scope_names=['profile'],
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, ['profile'])

        claims = userinfo_claims(
            self.access_token, scope_names=['email'],
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, expected_claims=['preferred_username'])

        claims = userinfo_claims(
            self.access_token,
            claims_request=userinfo_req({'email': None, 'preferred_username': None})
        )
        self.assertIncludedClaims(claims, expected_claims=['preferred_username'])

        # Check with extra scopes

        self.access_token.scope |= constants.PROFILE_SCOPE | constants.EMAIL_SCOPE
        self.access_token.save()

        claims = userinfo_claims(
            self.access_token,
            claims_request=userinfo_req({'email': None, 'preferred_username': None})
        )
        self.assertIncludedClaims(claims, expected_claims=['email', 'preferred_username'])

        claims = userinfo_claims(
            self.access_token,
            scope_names=['email'],
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, ['email'], ['preferred_username'])

        claims = userinfo_claims(self.access_token)
        self.assertIncludedClaims(claims, ['profile', 'email'])
