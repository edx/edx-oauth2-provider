# pylint: disable=missing-docstring
from .base import UserInfoTestCase


class UserInfoViewTest(UserInfoTestCase):
    def test_authorized(self):
        token = self.access_token.token
        self.set_access_token_scope('openid')

        response, _ = self.get_userinfo(token)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized(self):
        # No token
        response, values = self.get_userinfo()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(values['error'], 'access_denied')

        # Bad Token
        token = 'bad_token'
        response, _ = self.get_userinfo(token)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(values['error'], 'access_denied')

        # No openid scope in access token
        token = self.access_token.token
        self.set_access_token_scope('something')

        response, _ = self.get_userinfo(token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(values['error'], 'access_denied')

    def test_scope_request(self):
        scope = 'openid profile'
        self.set_access_token_scope(scope)

        token = self.access_token.token
        response, claims = self.get_userinfo(token, scope)
        self.assertEqual(response.status_code, 200)

        user = self.user
        expected = {
            u'preferred_username': user.username,
            u'given_name': user.first_name,
            u'family_name': user.last_name,
            u'name': user.get_full_name(),
        }

        for key, value in expected.iteritems():
            self.assertEqual(claims[key], value)

    def test_claims_request(self):
        valid_scope = 'openid profile'
        self.set_access_token_scope(valid_scope)

        token = self.access_token.token

        scope_request = 'openid whatever'
        claims_request = {
            'name': None,
            'foo': {'value': 'one'},
            'what': {'values': ['one', 'two']},
        }

        response, claims = self.get_userinfo(token, scope_request, claims_request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('sub', claims)
        self.assertIn('name', claims)
        self.assertEqual(len(claims), 2)

        scope_request = 'openid profile'
        claims_request = {
            'test': {'essential': True}
        }

        response, claims = self.get_userinfo(token, scope_request, claims_request)

        self.assertIn('test', claims)
