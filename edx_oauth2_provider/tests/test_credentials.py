""" Test email as username authentication """

import json

from django.core.urlresolvers import reverse

import ddt
from provider.constants import CONFIDENTIAL, PUBLIC

from .base import OAuth2TestCase
from .factories import ClientFactory

USERNAME = 'some_username'
EMAIL = 'test@example.com'
PASSWORD = 'some_password'

CLIENT_ID = 'some_client_id'
CLIENT_SECRET = 'some_secret'

# Data to generate login tests. Missing fields default to the values
# in the class variables below. 'success' defaults to False.
# 'client_secret' is not used unless specified.
AUTHENTICATION_TEST_DATA = [
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


@ddt.ddt
class AuthenticationTest(OAuth2TestCase):
    def setUp(self):
        super(AuthenticationTest, self).setUp()
        user = self.user_factory.create(
            username=USERNAME,
            password=PASSWORD,
            email=EMAIL
        )
        self.set_user(user)

        self.auth_client = ClientFactory.create(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )

        self.url = reverse('oauth2:access_token')

    @ddt.data(*AUTHENTICATION_TEST_DATA)
    def test_password_grants(self, data):
        self.auth_client.client_type = data.get('client_type', PUBLIC)
        self.auth_client.save()

        values = {
            'grant_type': 'password',
            'client_id': data.get('client_id', CLIENT_ID),
            'username': data.get('username', USERNAME),
            'password': data.get('password', PASSWORD),
        }

        client_secret = data.get('client_secret')
        if client_secret:
            values.update({'client_secret': client_secret})

        response = self.client.post(self.url, values)

        if data.get('success', False):
            self.assertEqual(200, response.status_code)
            self.assertIn('access_token', json.loads(response.content))
        else:
            self.assertEqual(400, response.status_code)
