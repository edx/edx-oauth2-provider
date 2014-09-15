# pylint: disable=missing-docstring

from django.core.urlresolvers import reverse

from oauth2_provider.tests.base import OAuth2TestCase
from oauth2_provider.tests.util import normpath


class TrustedClientTest(OAuth2TestCase):
    def test_trusted_client(self):
        response = self.login_and_authorize(trusted=True)

        # Check for valid redirect
        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('oauth2:redirect'), normpath(response['Location']))

    def test_untrusted_client(self):
        response = self.login_and_authorize(trusted=False)

        # Check if consent form is being shown
        form_action = 'action="{}"'.format(normpath(reverse("oauth2:authorize")))
        self.assertContains(response, form_action, status_code=200)
