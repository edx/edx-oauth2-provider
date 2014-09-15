# pylint: disable=missing-docstring
import json
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test import TestCase

import jwt

import provider.scope

from oauth2_provider.models import TrustedClient
from oauth2_provider.tests.util import normpath
from oauth2_provider.tests.factories import (
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
        self.payload = {
            'client_id': self.auth_client.client_id,
            'redirect_uri': self.auth_client.redirect_uri,
            'response_type': 'code',
            'state': 'some_state',
        }

    def login_and_authorize(self, trusted=False):
        """ Login into client using OAuth2 authorization flow. """

        self.set_trusted(self.auth_client, trusted)
        self.client.login(username=self.user.username, password=self.password)
        self.client.get(reverse('oauth2:capture'), self.payload)
        response = self.client.get(reverse('oauth2:authorize'), self.payload)
        return response

    def get_new_access_token_response(self):
        """ Get a new access token using the OAuth2 authorization flow. """
        response = self.login_and_authorize(trusted=True)
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), normpath(response['Location']))

        response = self.client.get(reverse('oauth2:redirect'))
        self.assertEqual(302, response.status_code)

        query = QueryDict(urlparse(response['Location']).query)

        response = self.client.post(reverse('oauth2:access_token'), {
            'grant_type': 'authorization_code',
            'client_id': self.auth_client.client_id,
            'client_secret': self.client_secret,
            'code': query['code'],
        })

        return response


class IDTokenTestCase(OAuth2TestCase):
    def set_scope(self, scope):
        if scope is None and 'scope' in self.payload:
            del self.payload['scope']
        else:
            self.payload['scope'] = scope

    def get_new_id_token_values(self, scope):
        """ Get a new id_token using the OIDC authorization flow. """

        self.assertIn('openid', scope.split())

        self.set_scope(scope)
        response = self.get_new_access_token_response()
        self.assertEqual(response.status_code, 200)

        values = json.loads(response.content)
        self.assertIn('access_token', values)

        id_token = values['id_token']
        secret = self.auth_client.client_secret
        self.assertValidIDToken(id_token, secret)

        scopes = values['scope'].split()
        claims = self.parse_id_token(id_token)

        # Should always be included
        self.assertIn('iss', claims)
        self.assertIn('sub', claims)

        return scopes, claims

    def parse_id_token(self, id_token):
        claims = jwt.decode(id_token, verify=False)
        return claims

    def assertValidIDToken(self, id_token, secret):
        try:
            jwt.decode(id_token, secret)
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
        self.access_token.save()

    def get_with_authorization(self, path, access_token=None, data=None):
        data = data if data else {}

        kwargs = {}
        if access_token:
            kwargs['HTTP_AUTHORIZATION'] = 'Bearer %s' % access_token

        return self.client.get(path, data, **kwargs)

    def get_userinfo(self, token=None, scope=None, claims=None):
        data = {}

        if scope:
            data.update({'scope': scope})

        if claims:
            data.update({
                'claims': json.dumps({
                    'userinfo': claims
                })
            })

        response = self.get_with_authorization(self.path, token, data)
        values = json.loads(response.content)
        return response, values
