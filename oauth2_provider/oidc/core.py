"""
OpenID Connect related utility functions

"""

import jwt

from oauth2_provider.oidc.collect import collect
from oauth2_provider.oidc.handlers import (BasicHandler, ProfileHandler, EmailHandler)

DEFAULT_ID_TOKEN_HANDLERS = (BasicHandler, ProfileHandler, EmailHandler)


def make_id_token(access_token, nonce=None):
    """
    Creates the claims for an ID token according to the OpenID Connect specification
    http://openid.net/specs/openid-connect-core-1_0.html#IDToken

    Returns dictionary of the claims required by the specification, along with
    the `profile` claims if requested in the scope.

    Arguments:
        access_token (AccessToken): Associated access token
        nonce (str): Optional nonce to protect against replay attacks

    """

    values = {'nonce': nonce} if nonce else None

    # Populate the claims in the ID token using the registered handlers
    handlers = DEFAULT_ID_TOKEN_HANDLERS
    claims = collect(handlers, access_token, values)

    return claims


def encode_id_token(id_token, secret, algorithm='HS256'):
    """
    Encode an ID token according to the OpenID Connect speficiation
    http://openid.net/specs/openid-connect-core-1_0.html#IDToken

    Returns encoded JWT token string.

    Arguments:
        id_token (dict): A dictionary with the OpenID Connect claims
        secret (str): Secret used to encode the id_token
    """
    return jwt.encode(id_token, secret, algorithm)
