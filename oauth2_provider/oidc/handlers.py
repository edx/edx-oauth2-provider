"""
Default claim handlers.

For details on the format of the claim handlers, see `oauth2_provider.handlers.collect`

"""

from calendar import timegm
from datetime import datetime, timedelta

from django.conf import settings


# pylint: disable=unused-argument
class BasicHandler(object):
    """
    Basic OpenID Connect ID token claims.

    For reference see:
    http://openid.net/specs/openid-connect-core-1_0.html#IDToken

    """

    def __init__(self):
        self._now = None

    @property
    def now(self):
        """Capture time"""
        if self._now is None:
            # Compute the current time only once per instance
            self._now = datetime.utcnow()
        return self._now

    def scope_openid(self):
        """Returns claims for the `openid` profile"""
        return ['iss', 'sub', 'aud', 'iat', 'exp', 'nonce']

    def claim_iss(self, user, client, value):
        """Required issuer identifier"""
        return settings.OAUTH_OIDC_ISSUER

    def claim_sub(self, user, client, value):
        """Required subject identifier"""
        # By default we are assuming that the username is unique.
        return user.username

    def claim_aud(self, user, client, value):
        """Required audience"""
        return client.client_id

    def claim_iat(self, user, client, value):
        """Required current/issued time"""
        return timegm(self.now.utctimetuple())

    def claim_exp(self, user, client, value):
        """Required expiration time"""
        expiration = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)
        expires = self.now + timedelta(seconds=expiration)
        return timegm(expires.utctimetuple())

    def claim_nonce(self, user, client, value):
        """Optional replay attack protection"""
        return value


# pylint: disable=unused-argument
class ProfileHandler(object):
    """
    Basic profile scope claim handler.

    For information see:
    http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims

    Some claims are missing since they require a detailed User
    profile, and can be completed in another claim handler.

    """

    def scope_profile(self):
        """Returns claims for the `profile` scope."""
        return ['name', 'family_name', 'given_name', 'preferred_username']

    def claim_family_name(self, user, client, value):
        """End user last or family name"""
        return user.last_name

    def claim_name(self, user, client, value):
        """End user full name"""
        return user.get_full_name()

    def claim_given_name(self, user, client, value):
        """End user first or given name"""
        return user.first_name

    def claim_preferred_username(self, user, client, value):
        """End user preferred username"""
        return user.username


# pylint: disable=unused-argument
class EmailHandler(object):
    """
    Basic email scope claim handler.

    For information see:
    http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims

    Some claims are missing since they require a more detail User profile.

    """

    def scope_email(self):
        """Returns claims for the `profile` scope."""
        return ['email']

    def claim_email(self, user, client, value):
        """End user email"""
        return user.email
