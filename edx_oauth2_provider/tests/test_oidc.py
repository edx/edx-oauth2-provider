# pylint: disable=missing-docstring

import datetime
import json
import uuid

from django.conf import settings
from django.test.utils import override_settings

import jwt
import mock

from provider.scope import check
from .. import oidc
from .. import constants
from ..oidc.core import IDToken
from .base import OAuth2TestCase
from .factories import AccessTokenFactory

BASE_DATETIME = datetime.datetime(1970, 1, 1)


@mock.patch('django.utils.timezone.now', mock.Mock(return_value=BASE_DATETIME))
@override_settings(OAUTH_OIDC_ISSUER='https://example.com/')
class BaseTestCase(OAuth2TestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.nonce = unicode(uuid.uuid4())
        self.access_token = AccessTokenFactory(user=self.user, client=self.auth_client)


class IdTokenTest(BaseTestCase):
    def _get_actual_claims(self, access_token, nonce):
        with mock.patch('edx_oauth2_provider.oidc.handlers.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = BASE_DATETIME
            id_token = oidc.id_token(access_token, nonce)

            # Clear id token since a handler can change it.
            id_token.claims['sub'] = None

            return id_token.claims

    def _get_expected_claims(self, access_token, nonce):
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

    def _decode(self, id_token, audience):
        return jwt.decode(id_token, 'test_secret', audience=audience, verify_expiration=False)

    def test_get_id_token(self):
        actual = self._get_actual_claims(self.access_token, self.nonce)
        expected = self._get_expected_claims(self.access_token, self.nonce)

        self.assertEqual(actual, expected)

        encoded = IDToken(self.access_token, scopes=[], claims=actual).encode('test_secret')
        self.assertEqual(self._decode(encoded, actual['aud']), expected)

    def test_get_id_token_with_profile(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE
        self.access_token.save()

        claims = self._get_actual_claims(self.access_token, self.nonce)
        expected = self._get_expected_claims(self.access_token, self.nonce)
        self.assertEqual(claims, expected)

    def test_get_id_token_with_profile_and_email(self):
        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE | constants.EMAIL_SCOPE
        self.access_token.save()

        claims = self._get_actual_claims(self.access_token, self.nonce)
        expected = self._get_expected_claims(self.access_token, self.nonce)
        self.assertEqual(claims, expected)


class UserInfoTest(BaseTestCase):
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

        claims_request = {'userinfo': {'preferred_username': {'value': 'pedro'}}}
        claims = userinfo_claims(self.access_token, claims_request=claims_request)

        self.assertEqual(claims['preferred_username'], self.user.username)
        self.assertIn('sub', claims)
        self.assertEqual(len(claims), 2)  # should not return any more claims

    def test_not_recognized_values(self):
        id_token = oidc.userinfo(
            self.access_token,
            scope_request=['openid'],  # it should not matter if we don't add 'profile'
            claims_request={'userinfo': {'foo': {'value': 'bar'}}},
        )

        self.assertIn('sub', id_token.claims)
        self.assertEqual(len(id_token.claims), 1)

    def test_arguments(self):
        """ Test if the responses contain the requested claims according to permissions"""
        # TODO: replace with DDT test

        def userinfo_req(req):
            return {'userinfo': req}

        # Add the profile scope to access token
        self.access_token.scope |= constants.PROFILE_SCOPE
        self.access_token.save()

        claims = userinfo_claims(self.access_token)
        self.assertIncludedClaims(claims, ['profile'])

        claims = userinfo_claims(self.access_token, scope_request=['openid', 'profile', 'email'])
        self.assertIncludedClaims(claims, ['profile'])

        claims = userinfo_claims(self.access_token, scope_request=['openid', 'email'])
        self.assertIncludedClaims(claims)

        claims = userinfo_claims(
            self.access_token,
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, expected_claims=['preferred_username'])

        claims = userinfo_claims(self.access_token, scope_request=['email'])
        self.assertIncludedClaims(claims)

        claims = userinfo_claims(
            self.access_token,
            scope_request=['profile'],
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, ['profile'])

        claims = userinfo_claims(
            self.access_token, scope_request=['email'],
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
            scope_request=['email'],
            claims_request=userinfo_req({'preferred_username': None})
        )
        self.assertIncludedClaims(claims, ['email'], ['preferred_username'])

        claims = userinfo_claims(self.access_token)
        self.assertIncludedClaims(claims, ['profile', 'email'])


def userinfo_claims(access_token, scope_request=None, claims_request=None):
    id_token = oidc.userinfo(access_token, scope_request, claims_request)
    return id_token.claims
