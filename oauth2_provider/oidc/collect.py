"""
Functions to dispach OpenID Connect scopes and claim request to
claim handlers.

Scopes are groups of claims. Claims are simple assertions about a OIDC
user or client. For more information see:

http://openid.net/specs/openid-connect-core-1_0.html#Claims

Claim handlers are simple python objects that define with two
different type of methods, one corresponding the scopes, and the other
one corresponding to claims.

The scope methods start with the prefix `scope_` and end with the name
of the scope, for example `scope_profile`. Each scope method returns a
list of the name of its associated claims.

The claim methods start with the prefix `claim_` and end with the name
of the claim, for example `claim_email`. The method receive three
paramaters `user`, `client` and `value`. The first and second and the
`User` and `Client` objects associated with the request. The `values`
parameter has values associated with the claim according to how it is
defined. Claim method return the value corresponding to the claim. If
the returned value is `None`, the claim will not be included in the
response.

The method `__getattr__` can be overloaded to support claims whose
names are not valid python method names.

For an example of handlers, see `oauth2_provider.handlers.basic`

"""

import provider.scope


def collect(handlers, access_token, values=None):
    """
    Collect all the claims associated with the access_token scope for
    the specified handler.

    Arguments:

      handlers (list): List of claim handler classes
      access_token (AccessToken): Associated access token
      values (dict): Initial values for each claim.

    Returns dictionary with values for the collected claims.

    """
    results = {}

    for handler_cls in handlers:
        handler = handler_cls()

        scope_names = provider.scope.to_names(access_token.scope)

        claims = _collect_claims(
            handler,
            claim_names=_collect_scopes(handler, scope_names),
            user=access_token.user,
            client=access_token.client,
            values=values or {}
        )

        # Current handler overrides previous values
        results.update(claims)

    return results


def _collect_scopes(handler, scopes):
    """Get all the claim names from the handler and requested scope"""
    claim_names = set()
    for scope in scopes:
        func = getattr(handler, 'scope_{}'.format(scope.lower()), None)
        if func:
            claim_names.update(func())

    return claim_names


def _collect_claims(handler, claim_names, user, client, values):
    """Get all values for the claims from the handler"""
    claims = {}
    for name in claim_names:
        func = getattr(handler, 'claim_{}'.format(name.lower()), None)
        if func:
            args = [user, client, values.get(name)]
            ret = func(*args)
            if ret is not None:
                claims[name] = ret

    return claims
