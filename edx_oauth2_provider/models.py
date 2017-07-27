"""
Custom OAuth2 models
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from provider.oauth2.models import Client

# Import constants to force override of `provider.scope`
# See constants.py for explanation
from . import constants  # pylint: disable=unused-import


@python_2_unicode_compatible
class TrustedClient(models.Model):
    """
    By default `django-oauth2-provider` shows a consent form to the
    user after his credentials has been validated. Trusted clients
    bypass the user consent and redirect to the OAuth2 client
    directly.

    """
    client = models.ForeignKey(Client)

    class Meta(object):
        db_table = 'oauth2_provider_trustedclient'

    def __str__(self):
        return "{}".format(self.client)
