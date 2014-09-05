"""
Functions to dispach OpenID Connect scopes and claim request to
claim handlers.

For details on the format of the claim handlers, see
`oauth2_provider.oicd.handlers`

None: The functions in this module assume the `openid` scope is implied.

"""

import provider.scope


REQUIRED_SCOPES = ['openid']

CLAIM_REQUEST_FIELDS = ['value', 'values', 'essential']


def collect(handlers, access_token, scopes=None, claims=None, inclusive=True):
    """
    Collect all the claims associated with the `access_token` scope for
    the specified handler.

    Arguments:

      handlers (list): List of claim handler classes.
      access_token (AccessToken): Associated access token.
      scopes (list): List of requested scopes.
      claims (dict): Dictionary of requested claims and values.
      inclusive (bool): Include all authorized claims, defaults
        to False except if `scope` and `claims` parameters are
        not specified.

    Returns dictionary with values for the collected claims.

    """
    user = access_token.user
    client = access_token.client

    scopes = set() if scopes is None else set(scopes)

    # In `collect` the 'openid' scope is implied
    if scopes and 'openid' in scopes:
        scopes.remove('openid')

    claims = validate_claim_request(claims)

    # Add all authorized claims if no scope or claims are requested
    if not(scopes or claims):
        inclusive = True

    required_claims = collect_claim_names(handlers, REQUIRED_SCOPES, user, client)

    authorized_scopes = set(provider.scope.to_names(access_token.scope))
    authorized_claims = collect_claim_names(handlers, authorized_scopes, user, client)

    requested_claims = set()
    if inclusive:
        requested_claims.update(authorized_claims)
    else:
        requested_claims = collect_claim_names(handlers, scopes, user, client)
        requested_claims.update(claims.keys())

    # Remove all claims that are not part of the authorized scope
    claim_names = required_claims | (requested_claims & authorized_claims)

    claim_results = collect_claim_values(
        handlers,
        names=claim_names,
        user=user,
        client=client,
        values=claims or {}
    )

    return claim_results


def collect_authorized_scope(handlers, scopes, user, client):
    """ Get a set of all the authorized scopes according to the handlers """
    results = set()

    data = {'user': user, 'client': client}

    def visitor(scope_name, func):
        claim_names = func(data)
        if claim_names:
            results.add(scope_name)

    _visit_handlers(handlers, visitor, 'scope', scopes)

    return results


def collect_claim_names(handlers, scopes, user, client):
    """ Get the names of the claims supported by the handlers for the requested scope. """
    results = set()

    data = {'user': user, 'client': client}

    def visitor(_scope_name, func):
        claim_names = func(data)
        results.update(claim_names if claim_names else [])

    _visit_handlers(handlers, visitor, 'scope', scopes)

    return results


def collect_claim_values(handlers, names, user, client, values):
    """ Get the values from the handlers of the requested claims. """

    results = {}

    def visitor(claim_name, func):
        data = {'user': user, 'client': client}
        data.update(values.get(claim_name) or {})
        claim_value = func(data)
        if claim_value is not None:
            # New values overwrite previous results
            results[claim_name] = claim_value

    _visit_handlers(handlers, visitor, 'claim', names)

    return results


def validate_claim_request(claims, ignore_errors=False):
    """
    Validates a claim request section (`userinfo` or `id_token`) according
    to section 5.5 of the OpenID Connect specification:

    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Returns a copy of the claim request with only the valid fields and values.

    Raises ValueError is the claim request is invalid and `ignore_errors` is False

    """

    results = {}
    claims = claims if claims else {}

    for name, value in claims.iteritems():
        if value is None:
            results[name] = None
        elif isinstance(value, dict):
            results[name] = _validate_claim_values(name, value, ignore_errors)
        else:
            if not ignore_errors:
                msg = 'Invalid claim {}.'.format(name)
                raise ValueError(msg)

    return results


def _validate_claim_values(name, value, ignore_errors):
    """ Helper for `validate_claim_request` """
    results = {'essential': False}
    for key, value in value.iteritems():
        if key in CLAIM_REQUEST_FIELDS:
            results[key] = value
        else:
            if not ignore_errors:
                msg = 'Unknown attribute {} in claim value {}.'.format(key, name)
                raise ValueError(msg)
    return results


def _visit_handlers(handlers, visitor, preffix, suffixes):
    """ Use visitor partern to collect information from handlers """

    handlers = [cls() for cls in handlers]

    results = []
    for handler in handlers:
        for suffix in suffixes:
            func = getattr(handler, '{}_{}'.format(preffix, suffix).lower(), None)
            if func:
                results.append(visitor(suffix, func))

    return results
