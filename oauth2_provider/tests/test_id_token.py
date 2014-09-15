# pylint: disable=missing-docstring

import json

from django.test.utils import override_settings

from oauth2_provider.tests.base import IDTokenTestCase

ISSUER = 'https://example.com/'


@override_settings(OAUTH_OIDC_ISSUER=ISSUER)
class OIDCScopeTest(IDTokenTestCase):
    """Test OpenID Connect ID Token scopes"""

    def test_default_scope(self):
        response = self.get_new_access_token_response()
        self.assertEqual(200, response.status_code)

        values = json.loads(response.content)
        scope = values.get('scope', '').split()

        # The default scope should be empty
        self.assertEqual(len(scope), 0)

    def test_id_token(self):
        scopes, claims = self.get_new_id_token_values('openid')

        self.assertIn('openid', scopes)

        required_claims = ['iss', 'iat', 'sub', 'exp', 'aud']
        for name in required_claims:
            self.assertIn(name, claims)

        self.assertEqual(ISSUER, claims['iss'])

    def test_sub_claim(self):
        # Verify that the 'sub' claim is unique for each user
        user_a = self.user
        _scope, claims_a = self.get_new_id_token_values('openid')

        self.set_user(self.make_user())
        _scope, claims_b = self.get_new_id_token_values('openid')
        self.assertNotEqual(claims_a['sub'], claims_b['sub'])

        # generate another token for user_a
        self.set_user(user_a)
        _scope, claims_c = self.get_new_id_token_values('openid')
        self.assertEqual(claims_a['sub'], claims_c['sub'])

    def test_profile_scope(self):
        scopes, claims = self.get_new_id_token_values('openid profile')

        self.assertIn('openid', scopes)
        self.assertIn('profile', scopes)

        self.assertIn('preferred_username', claims)

    def test_email_scope(self):
        scopes, claims = self.get_new_id_token_values('openid email')

        self.assertIn('openid', scopes)
        self.assertIn('email', scopes)

        self.assertIn('email', claims)
