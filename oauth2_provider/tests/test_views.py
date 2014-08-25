import json
import os.path
import urlparse

from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test import TestCase
from ddt import ddt, data

from provider.constants import PUBLIC, CONFIDENTIAL
from provider.oauth2.tests import BaseOAuth2TestCase
from oauth2_provider.tests.factories import UserFactory, ClientFactory, TrustedClientFactory


USERNAME = 'some_username'
EMAIL = 'test@example.com'
PASSWORD = 'some_password'

CLIENT_ID = 'some_client_id'
CLIENT_SECRET = 'some_client_secret'

# Data to generate login tests. Missing fields default to the values
# in the module variables above. 'success' defaults to False.
# 'client_secret' is not used unless specified.
CUSTOM_PASSWORD_GRANT_TEST_DATA = [
    {
        'success': True
    },
    {
        'username': EMAIL,
        'success': True
    },
    {
        'password': PASSWORD + '_bad',
    },
    {
        'username': USERNAME + '_bad',
    },
    {
        'client_id': CLIENT_ID + '_bad'
    },
    {
        'username': EMAIL,
        'password': PASSWORD + '_bad',
    },
    {
        'client_secret': CLIENT_SECRET,
        'success': True
    },
    {
        'client_type': CONFIDENTIAL,
        'client_secret': CLIENT_SECRET,
        'success': True
    },
    {
        'client_secret': CLIENT_SECRET + '_bad',
        'success': True  # public clients should ignore the client_secret field
    },
    {
        'client_type': CONFIDENTIAL,
        'client_secret': CLIENT_SECRET + '_bad',
    },
]


def path(url):
    """Get and normalize the path on a URL"""
    return os.path.normpath(urlparse.urlparse(url).path)


@ddt
class AccessTokenTest(BaseOAuth2TestCase):
    fixtures = ['test_oauth2.json']

    def setUp(self):
        self.url = reverse('oauth2:access_token')
        self.user = UserFactory.create(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD,
        )

    @data(*CUSTOM_PASSWORD_GRANT_TEST_DATA)
    def test_custom_password_grants(self, test_data):
        ClientFactory.create(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            client_type=test_data.get('client_type', PUBLIC)
        )

        values = {
            'grant_type': 'password',
            'client_id': test_data.get('client_id', CLIENT_ID),
            'username': test_data.get('username', USERNAME),
            'password': test_data.get('password', PASSWORD),
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

    def _login_authorize_get_token(self):
        required_props = ['access_token', 'token_type']

        self.login()
        self._login_and_authorize()

        response = self.client.get(self.redirect_url())
        query = QueryDict(urlparse.urlparse(response['Location']).query)
        code = query['code']

        response = self.client.post(self.access_token_url(), {
            'grant_type': 'authorization_code',
            'client_id': self.get_client().client_id,
            'client_secret': self.get_client().client_secret,
            'code': code})

        self.assertEqual(200, response.status_code, response.content)

        token = json.loads(response.content)

        for prop in required_props:
            self.assertIn(prop, token, "Access token response missing required property: %s" % prop)

        return token


class ClientBaseTest(TestCase):
    def setUp(self):
        self.user = UserFactory.create(
            username=USERNAME,
            password=PASSWORD,
        )
        self.auth_client = ClientFactory.create(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            client_type=CONFIDENTIAL
        )

        self.payload = {
            'client_id': CLIENT_ID,
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
        self.client.login(username=USERNAME, password=PASSWORD)
        self.client.get(reverse('oauth2:capture'), self.payload)
        response = self.client.get(reverse('oauth2:authorize'), self.payload)

        return response


class TrustedClientTest(ClientBaseTest):
    def test_untrusted_client(self):
        response = self.login_and_authorize()

        form_action = 'action="{}"'.format(path(reverse("oauth2:authorize")))

        # Check that the consent form is presented
        self.assertContains(response, form_action, status_code=200)

    def test_trusted_client(self):
        self.use_trusted_client()

        response = self.login_and_authorize()
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), path(response['Location']))


class ClientScopeTest(ClientBaseTest):
    def get_access_token_response(self):
        response = self.login_and_authorize()
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), path(response['Location']))

        response = self.client.get(reverse('oauth2:redirect'))

        query = QueryDict(urlparse.urlparse(response['Location']).query)
        code = query['code']

        response = self.client.post(reverse('oauth2:access_token'), {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
        })

        return response

    def test_username_scope(self):
        self.use_trusted_client()
        self.set_scope('preferred_username')

        response = self.get_access_token_response()

        self.assertEqual(200, response.status_code)

        values = json.loads(response.content)
        self.assertEqual(values.get('preferred_username'), USERNAME)
        self.assertIn('preferred_username', values.get('scope'))

    def test_no_scope(self):
        self.use_trusted_client()

        response = self.get_access_token_response()

        self.assertEqual(200, response.status_code)

        values = json.loads(response.content)
        self.assertNotIn('preferred_username', values)
        self.assertNotIn('preferred_username', values.get('scope'))
