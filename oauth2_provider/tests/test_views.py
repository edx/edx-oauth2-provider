# pylint: disable=missing-docstring

import json
import os.path
import urlparse

from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test.utils import override_settings

import ddt
import jwt

from provider.constants import PUBLIC

from oauth2_provider.tests import data
from oauth2_provider.tests.base import BaseTestCase
from oauth2_provider.tests.factories import ClientFactory, TrustedClientFactory


class ClientTestCase(BaseTestCase):

    def setUp(self):
        super(ClientTestCase, self).setUp()
        self.payload = {
            'client_id': data.CLIENT_ID,
            'response_type': 'code',
            'state': 'some_state',
            'redirect_uri': ClientFactory.redirect_uri
        }

    def set_scope(self, scope):
        if scope is None and 'scope' in self.payload:
            del self.payload['scope']
        else:
            self.payload['scope'] = scope

    def use_trusted_client(self):
        client = TrustedClientFactory.create(client=self.auth_client)
        return client

    def login_and_authorize(self):
        self.client.login(username=data.USERNAME, password=data.PASSWORD)
        self.client.get(reverse('oauth2:capture'), self.payload)
        response = self.client.get(reverse('oauth2:authorize'), self.payload)

        return response


@ddt.ddt
class AccessTokenTest(ClientTestCase):
    def setUp(self):
        super(AccessTokenTest, self).setUp()
        self.url = reverse('oauth2:access_token')

    @ddt.data(*data.CUSTOM_PASSWORD_GRANT_TEST_DATA)
    def test_custom_password_grants(self, test_data):
        self.auth_client.client_type = test_data.get('client_type', PUBLIC)
        self.auth_client.save()

        values = {
            'grant_type': 'password',
            'client_id': test_data.get('client_id', data.CLIENT_ID),
            'username': test_data.get('username', data.USERNAME),
            'password': test_data.get('password', data.PASSWORD),
        }

        client_secret = test_data.get('client_secret')
        if client_secret:
            values.update({'client_secret': client_secret})

        response = self.client.post(self.url, values)

        if test_data.get('success', False):
            self.assertEqual(200, response.status_code)
            self.assertIn('access_token', json.loads(response.content))
        else:
            self.assertEqual(400, response.status_code)


class TrustedClientTest(ClientTestCase):
    def test_untrusted_client(self):
        response = self.login_and_authorize()

        form_action = 'action="{}"'.format(normpath(reverse("oauth2:authorize")))

        # Check that the consent form is presented
        self.assertContains(response, form_action, status_code=200)

    def test_trusted_client(self):
        self.use_trusted_client()

        response = self.login_and_authorize()
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), normpath(response['Location']))


class ClientScopeTest(ClientTestCase):
    """Test OAuth2 scopes when getting access token"""

    def get_access_token_response(self):
        response = self.login_and_authorize()
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), normpath(response['Location']))

        response = self.client.get(reverse('oauth2:redirect'))

        query = QueryDict(urlparse.urlparse(response['Location']).query)
        code = query['code']

        response = self.client.post(reverse('oauth2:access_token'), {
            'grant_type': 'authorization_code',
            'client_id': data.CLIENT_ID,
            'client_secret': data.CLIENT_SECRET,
            'code': code,
        })

        return response

    def test_username_scope(self):
        self.use_trusted_client()
        self.set_scope('preferred_username')

        response = self.get_access_token_response()

        self.assertEqual(200, response.status_code)

        values = json.loads(response.content)
        self.assertEqual(values.get('preferred_username'), data.USERNAME)
        self.assertIn('preferred_username', values.get('scope'))

    def test_no_scope(self):
        self.use_trusted_client()

        response = self.get_access_token_response()

        self.assertEqual(200, response.status_code)

        values = json.loads(response.content)
        self.assertNotIn('preferred_username', values)
        self.assertNotIn('preferred_username', values.get('scope'))


@override_settings(OAUTH_OIDC_ISSUER=data.ISSUER)
class ClientOIDCScopeTest(ClientScopeTest):
    """Test OpenID Connect scopes when getting the access token"""

    def test_openid_scopes(self):
        self.use_trusted_client()
        self.set_scope('openid profile email')

        response = self.get_access_token_response()

        self.assertEqual(200, response.status_code)

        values = json.loads(response.content)
        scopes = values.get('scope').split()

        self.assertItemsEqual(['openid', 'profile', 'email'], scopes)

        secret = self.auth_client.client_secret
        claims = jwt.decode(values.get('id_token'), secret)

        self.assertIn('iss', claims)
        self.assertIn('sub', claims)
        self.assertIn('name', claims)
        self.assertIn('email', claims)

        self.assertEqual(data.ISSUER, claims['iss'])


def normpath(url):
    """Get the normalized path of a URL"""
    return os.path.normpath(urlparse.urlparse(url).path)
