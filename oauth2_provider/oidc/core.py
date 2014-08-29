"""
OpenID Connect core related utility functions.

"""

import jwt

from oauth2_provider.oidc.collect import collect, collect_authorized_scope

from oauth2_provider.oidc.handlers import (
    BasicIDTokenHandler,
    BasicUserInfoHandler,
    ProfileHandler,
    EmailHandler
)

DEFAULT_ID_TOKEN_HANDLERS = (BasicIDTokenHandler, ProfileHandler, EmailHandler)
DEFAULT_USERINFO_HANDLERS = (BasicUserInfoHandler, ProfileHandler, EmailHandler)


def authorized_scopes(scope_names, user, client):
    """
    Returns only the scopes that are  authorized for the user or client.

    The authorization is determined by the `id_token` handlers.

    Arguments:
        scope_names (list): List of scope names.
        user (User): User for the request.
        client (Client): OAuth2 Client for the request.

    """
    handlers = DEFAULT_ID_TOKEN_HANDLERS

    return collect_authorized_scope(handlers, scope_names, user, client)


def id_token_claims(access_token, nonce=None, claims_request=None):
    """
    Creates claims data for an OpenID Connect ID Token according to:

    http://openid.net/specs/openid-connect-basic-1_0.html#IDToken

    Arguments:
        access_token (AccessToken): Associated OAuth2 access token.
        nonce (str): Optional nonce to protect against replay attacks.
        claims_request (dict): Optional dictionary with a claims request parameter.

    Information on the claims request parameter specification:

    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Returns dictionary of the claims required by the specification.

    """

    claims = claims_request.get('id_token', {}) if claims_request else {}

    handlers = DEFAULT_ID_TOKEN_HANDLERS

    if nonce:
        claims.update({'nonce': {'value': nonce}})

    result = collect(handlers, access_token, claims=claims, inclusive=True)

    return result


def userinfo_claims(access_token, scope_names=None, claims_request=None):
    """
    Creates claims data for OpenID Connect UserInfo endpoint, according:

    http://openid.net/specs/openid-connect-basic-1_0.html#UserInfoResponse

    Support scope and claims request parameter as described in:

    http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Arguments:
        access_token (AccessToken): Associated access token
        scope_names (list): Optional list of requested scopes
        claims_request (dict): Optional dictionary with a claims request parameter

    Information on the claims request parameter specification:

    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Returns dictionary of the claims required by the specification.

    """

    handlers = DEFAULT_USERINFO_HANDLERS

    claims = claims_request.get('userinfo', {}) if claims_request else {}

    result = collect(handlers, access_token, scope_names, claims, inclusive=False)
    return result


def encode_claims(claims, secret, algorithm='HS256'):
    """
    Encode an set of claims according to the OpenID Connect
    specification, which is used to create ID Tokens:

    http://openid.net/specs/openid-connect-basic-1_0.html#IDToken

    Arguments:
        id_token (dict): A dictionary with the OpenID Connect claims
        secret (str): Secret used to encode the id_token

    Returns encoded JWT token string.
    """
    return jwt.encode(claims, secret, algorithm)
