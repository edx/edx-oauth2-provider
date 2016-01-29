"""
OpenID Connect core related utility functions.

Defines utility functions to process the ID Token and UserInfo
endpoints according to the OpenID Connect specification.

"""

import jwt

import provider.scope

from .. import constants
from ..utils import import_string
from .collect import collect


HANDLERS = {
    'id_token': [import_string(cls) for cls in constants.ID_TOKEN_HANDLERS],
    'userinfo': [import_string(cls) for cls in constants.USERINFO_HANDLERS]
}


class IDToken(object):
    """
    Simple container for OpenID Connect related responses.

    Attributes:
        access_token (:class:`AccessToken`): Associated Access Token object.
        scopes (list): List of scope names.
        claims (dict): Dictionary of claim names and values.

    """

    def __init__(self, access_token, scopes, claims):
        self.access_token = access_token
        self.scopes = scopes
        self.claims = claims

    def encode(self, secret, algorithm='HS256'):
        """
        Encode the set of claims to the JWT (JSON Web Token) format
        according to the OpenID Connect specification:

        http://openid.net/specs/openid-connect-basic-1_0.html#IDToken

        Arguments:
            claims (dict): A dictionary with the OpenID Connect claims.
            secret (str): Secret used to encode the id_token.
            algorithm (str): Algorithm used for encoding.
                Defaults to HS256.

        Returns encoded JWT token string.

        """

        return jwt.encode(self.claims, secret, algorithm)


def id_token(access_token, nonce=None, claims_request=None):
    """
    Returns data required for an OpenID Connect ID Token according to:

    - http://openid.net/specs/openid-connect-basic-1_0.html#IDToken

    Arguments:
        access_token (:class:`AccessToken`): Associated OAuth2 access token.
        nonce (str): Optional nonce to protect against replay attacks.
        claims_request (dict): Optional dictionary with the claims request parameters.

    Information on the `claims_request` parameter specification:

    - http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Returns an :class:`IDToken` instance with the scopes from the
    access_token and the corresponding claims. Claims in the
    `claims_request` paramater id_token section will be included *in
    addition* to the ones corresponding to the scopes specified in the
    `access_token`.

    """

    handlers = HANDLERS['id_token']

    # Select only the relevant section of the claims request.
    claims_request_section = claims_request.get('id_token', {}) if claims_request else {}

    scope_request = provider.scope.to_names(access_token.scope)

    if nonce:
        claims_request_section.update({'nonce': {'value': nonce}})

    scopes, claims = collect(
        handlers,
        access_token,
        scope_request=scope_request,
        claims_request=claims_request_section,
    )

    return IDToken(access_token, scopes, claims)


def userinfo(access_token, scope_request=None, claims_request=None):
    """
    Returns data required for an OpenID Connect UserInfo response, according to:

    http://openid.net/specs/openid-connect-basic-1_0.html#UserInfoResponse

    Supports scope and claims request parameter as described in:

    - http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    - http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Arguments: access_token (:class:`AccessToken`): Associated access
        token.  scope_request (list): Optional list of requested
        scopes. Only scopes authorized in the `access_token` will be
            considered.  claims_request
        (dict): Optional dictionary with a claims request parameter.

    Information on the claims request parameter specification:

    - http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    As a convinience, if neither `scope_request` or user_info claim is
    specified in the `claims_request`, it will return the claims for
    all the scopes in the `access_token`.

    Returns an :class:`IDToken` instance with the scopes from the
    `scope_request` and the corresponding claims. Claims in the
    `claims_request` paramater userinfo section will be included *in
    addition* to the ones corresponding to `scope_request`.

    """

    handlers = HANDLERS['userinfo']

    # Select only the relevant section of the claims request.
    claims_request_section = claims_request.get('userinfo', {}) if claims_request else {}

    # If nothing is requested, return the claims for the scopes in the access token.
    if not scope_request and not claims_request_section:
        scope_request = provider.scope.to_names(access_token.scope)
    else:
        scope_request = scope_request

    scopes, claims = collect(
        handlers,
        access_token,
        scope_request=scope_request,
        claims_request=claims_request_section,
    )

    return IDToken(access_token, scopes, claims)
