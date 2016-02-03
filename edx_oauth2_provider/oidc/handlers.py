"""
Default OpenID Connect claim handlers.

Scopes are groups of claims. Claims are simple assertions about a
OpenID Connect user or client. For more information see:

http://openid.net/specs/openid-connect-core-1_0.html#Claims

Claim handlers are simple python objects that serve the following
purposes:

  - Determine what scopes and claims are available to each specific
    user and client.
  - Determine what claims are associated with each scope.
  - Evaluate the values of claims for each user and client.

Claim handlers do this by defining two different type of methods, one
corresponding to scope, and the other one corresponding to claims.

Scope Methods

The scope methods start with the prefix `scope_` and end with the name
of the scope, for example `scope_profile`. The method receives a
single parameter `data`, a dictionary with the following fields:

  - 'user': Requied. User instance for the current request.
  - 'client': Required. OAuth2 Client instance for the current request.

Each scope method should return a list of its asociated claim names,
or None if the `user` or `client` don't have authorization for that
scope.

Claim Methods

The claim methods start with the prefix `claim_` and end with the name
of the claim, for example `claim_email`.  The method receives a
single parameter `data`, a dictionary with the following fields:

  - 'user': Requied. User instance for the current request.
  - 'client': Required. OAuth2 Client instance for the current request.
  - 'value': Optional. Request that the claim returns with a particular value.
  - 'values': Optional. Request that the claim returns with particular values.
  - 'essential': Optional.  Indicate if the claim is essential.

For information on the 'value', 'values' and 'essential' fields, and
other claim values, see:

http://openid.net/specs/openid-connect-core-1_0.html#IndividualClaimsRequests

Claim methods return the value corresponding to the claim according to
the passed data fields. The interpretetion of the value(s) field is open to
each particular claim, and should be documented. If the returned value
is `None`, the claim will not be included in the response.


NOTE: The method `__getattr__` can be overloaded to support claims or
scopes whose names are not valid python method names.

"""

# pylint: disable=unused-argument

from calendar import timegm
from datetime import datetime, timedelta

from django.conf import settings


class BasicIDTokenHandler(object):
    """
    Basic OpenID Connect ID token claims.

    For reference see:
    http://openid.net/specs/openid-connect-basic-1_0.html#IDToken

    """

    def __init__(self):
        self._now = None

    @property
    def now(self):
        """ Capture time. """
        if self._now is None:
            # Compute the current time only once per instance
            self._now = datetime.utcnow()
        return self._now

    def scope_openid(self, data):
        """ Returns claims for the `openid` profile. """
        return ['iss', 'sub', 'aud', 'iat', 'exp', 'nonce']

    def claim_iss(self, data):
        """ Required issuer identifier. """
        return settings.OAUTH_OIDC_ISSUER

    def claim_sub(self, data):
        """ Required subject identifier. """
        # Use the primary key as the identifier
        return str(data['user'].pk)

    def claim_aud(self, data):
        """ Required audience. """
        return data['client'] .client_id

    def claim_iat(self, data):
        """ Required current/issued time. """
        return timegm(self.now.utctimetuple())

    def claim_exp(self, data):
        """ Required expiration time. """
        expiration = getattr(settings, 'OAUTH_ID_TOKEN_EXPIRATION', 30)
        expires = self.now + timedelta(seconds=expiration)
        return timegm(expires.utctimetuple())

    def claim_nonce(self, data):
        """ Optional replay attack protection. """
        return data.get('value')


class BasicUserInfoHandler(object):
    """
    Basic OpenID Connect User Info claims.

    For reference see:
    http://openid.net/specs/openid-connect-basic-1_0.html#UserInfo

    """

    def scope_openid(self, data):
        """Returns claims for the `openid` profile"""
        return ['sub']

    def claim_sub(self, data):
        """ Required subject identifier. """
        # Use the primary key as the identifier
        return str(data['user'].pk)


class ProfileHandler(object):
    """
    Basic profile scope claim handler.

    For information see:
    http://openid.net/specs/openid-connect-basic-1_0.html#Scopes

    Some claims are missing since they require a detailed User
    profile, and can included from another claim handler.

    """

    def scope_profile(self, data):
        """ Returns claims for the `profile` scope. """
        return ['name', 'family_name', 'given_name', 'preferred_username']

    def claim_family_name(self, data):
        """ End user last or family name. """
        return data['user'].last_name

    def claim_name(self, data):
        """ End user full name. """
        return data['user'].get_full_name()

    def claim_given_name(self, data):
        """ End user first or given name. """
        return data['user'].first_name

    def claim_preferred_username(self, data):
        """ End user preferred username. """
        return data['user'].username


class EmailHandler(object):
    """
    Basic email scope claim handler.

    For information see:
    http://openid.net/specs/openid-connect-basic-1_0.html#Scopes

    Some claims are missing since they require a more detailed User profile.

    """

    def scope_email(self, data):
        """ Returns claims for the `profile` scope. """
        return ['email']

    def claim_email(self, data):
        """ End user email. """
        return data['user'].email
