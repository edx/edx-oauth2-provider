# pylint: disable=missing-docstring
import json
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test import TestCase

import jwt

import provider.scope

from ..constants import AUTHORIZED_CLIENTS_SESSION_KEY
from ..models import TrustedClient
from .util import normpath
from .factories import (
    UserFactory,
    ClientFactory,
    AccessTokenFactory,
    TrustedClientFactory
)


class BaseTestCase(TestCase):
    def setUp(self):
        self.client_secret = 'some_secret'
        self.auth_client = ClientFactory(client_secret=self.client_secret)

        self.password = 'some_password'
        self.user_factory = UserFactory

        self.user = None
        self.access_token = None
        self.set_user(self.make_user())

    def make_user(self):
        return self.user_factory(password=self.password)

    def set_user(self, user):
        self.user = user

    def set_trusted(self, client, trusted=True):
        if trusted:
            TrustedClientFactory.create(client=client)
        else:
            TrustedClient.objects.filter(client=client).delete()


class OAuth2TestCase(BaseTestCase):
    def setUp(self):
        super(OAuth2TestCase, self).setUp()

    def login_and_authorize(self, scope=None, claims=None, trusted=False, validate_session=True):
        """ Login into client using OAuth2 authorization flow. """

        self.set_trusted(self.auth_client, trusted)
        self.client.login(username=self.user.username, password=self.password)

        client_id = self.auth_client.client_id
        payload = {
            'client_id': client_id,
            'redirect_uri': self.auth_client.redirect_uri,
            'response_type': 'code',
            'state': 'some_state',
        }
        _add_values(payload, 'id_token', scope, claims)

        response = self.client.get(reverse('oauth2:capture'), payload)
        self.assertEqual(302, response.status_code)

        response = self.client.get(reverse('oauth2:authorize'), payload)

        if validate_session:
            self.assertListEqual(self.client.session[AUTHORIZED_CLIENTS_SESSION_KEY], [client_id])

        return response

    def get_access_token_response(self, scope=None, claims=None):
        """ Get a new access token using the OAuth2 authorization flow. """
        response = self.login_and_authorize(scope, claims, trusted=True)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), normpath(response['Location']))

        response = self.client.get(reverse('oauth2:redirect'))
        self.assertEqual(302, response.status_code)

        query = QueryDict(urlparse(response['Location']).query)

        payload = {
            'grant_type': 'authorization_code',
            'client_id': self.auth_client.client_id,
            'client_secret': self.client_secret,
            'code': query['code'],
        }
        _add_values(payload, 'id_token', scope, claims)

        response = self.client.post(reverse('oauth2:access_token'), payload)
        return response


class IDTokenTestCase(OAuth2TestCase):
    def get_id_token_values(self, scope=None, claims=None):
        """ Get a new id_token using the OIDC authorization flow. """

        self.assertIn('openid', scope.split())

        response = self.get_access_token_response(scope, claims)
        self.assertEqual(response.status_code, 200)

        values = json.loads(response.content)
        self.assertIn('access_token', values)

        id_token = values['id_token']
        secret = self.auth_client.client_secret
        audience = self.auth_client.client_id
        self.assertValidIDToken(id_token, secret, audience)

        scopes = values['scope'].split()
        claims = self.parse_id_token(id_token)

        # Should always be included
        self.assertIn('iss', claims)
        self.assertIn('sub', claims)

        return scopes, claims

    def parse_id_token(self, id_token):
        claims = jwt.decode(id_token, verify=False)
        return claims

    def assertValidIDToken(self, id_token, secret, audience):
        try:
            jwt.decode(id_token, secret, audience=audience)
        except jwt.DecodeError:
            assert False


class UserInfoTestCase(BaseTestCase):
    def setUp(self):
        super(UserInfoTestCase, self).setUp()
        self.path = reverse('oauth2:user_info')
        self.set_user(self.user)

    def set_user(self, user):
        super(UserInfoTestCase, self).set_user(user)
        self.access_token = AccessTokenFactory(user=self.user, client=self.auth_client)

    def set_access_token_scope(self, scope):
        self.access_token.scope = provider.scope.to_int(*scope.split())
        self.access_token.save()  # pylint: disable=no-member

    def get_with_authorization(self, path, access_token=None, payload=None):
        kwargs = {}
        if access_token:
            kwargs['HTTP_AUTHORIZATION'] = 'Bearer %s' % access_token

        return self.client.get(path, payload, **kwargs)

    def get_userinfo(self, token=None, scope=None, claims=None):
        payload = _add_values({}, 'userinfo', scope, claims)
        response = self.get_with_authorization(self.path, token, payload)
        values = json.loads(response.content)
        return response, values


def _add_values(data, endpoint, scope=None, claims=None):
    if scope:
        data['scope'] = scope
    if claims:
        data['claims'] = json.dumps({endpoint: claims})
    return data
