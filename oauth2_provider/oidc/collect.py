"""
Functions to collect OpenID Connect values from claim handlers.

For details on the format of the claim handlers, see
:mod:`oauth2_provider.oicd.handlers`

None: The functions in this module assume the `openid` scope is implied.

"""

import provider.scope


REQUIRED_SCOPES = ['openid']

CLAIM_REQUEST_FIELDS = ['value', 'values', 'essential']


def collect(handlers, access_token, scope_request=None, claims_request=None):
    """
    Collect all the claims values from the `handlers`.

    Arguments:
      handlers (list): List of claim :class:`Handler` classes.
      access_token (:class:AccessToken): Associated access token.
      scope_request (list): List of requested scopes.
      claims_request (dict): Dictionary with only the relevant section of a
          OpenID Connect claims request.

    Returns a list of the scopes from `scope_request` that are authorized, and a
    dictionary of the claims associated with the authorized scopes in
    `scope_request`, and additionally, the authorized claims listed in
    `claims_request`.

    """
    user = access_token.user
    client = access_token.client

    # Instantiate handlers. Each handler is instanciated only once, allowing the
    # handler to keep state in-between calls to its scope and claim methods.

    handlers = [cls() for cls in handlers]

    # Find all authorized scopes by including the access_token scopes.  Note
    # that the handlers determine if a scope is authorized, not its presense in
    # the access_token.

    required_scopes = set(REQUIRED_SCOPES)
    token_scopes = set(provider.scope.to_names(access_token.scope))
    authorized_scopes = _collect_scopes(handlers, required_scopes | token_scopes, user, client)

    # Select only the authorized scopes from the requested scopes.

    scope_request = set(scope_request) if scope_request else set()
    scopes = required_scopes | (authorized_scopes & scope_request)

    # Find all authorized claims names for the authorized_scopes.

    authorized_names = _collect_names(handlers, authorized_scopes, user, client)

    # Select only the requested claims if no scope has been requested. Selecting
    # scopes has prevalence over selecting claims.

    claims_request = _validate_claim_request(claims_request)

    # Add the requested claims that are authorized to the response.

    requested_names = set(claims_request.keys()) & authorized_names
    names = _collect_names(handlers, scopes, user, client) | requested_names

    # Get the values for the claims.

    claims = _collect_values(
        handlers,
        names=names,
        user=user,
        client=client,
        values=claims_request or {}
    )

    return authorized_scopes, claims


def _collect_scopes(handlers, scopes, user, client):
    """ Get a set of all the authorized scopes according to the handlers. """
    results = set()

    data = {'user': user, 'client': client}

    def visitor(scope_name, func):
        claim_names = func(data)
        # If the claim_names is None, it means that the scope is not authorized.
        if claim_names is not None:
            results.add(scope_name)

    _visit_handlers(handlers, visitor, 'scope', scopes)

    return results


def _collect_names(handlers, scopes, user, client):
    """ Get the names of the claims supported by the handlers for the requested scope. """

    results = set()

    data = {'user': user, 'client': client}

    def visitor(_scope_name, func):
        claim_names = func(data)
        # If the claim_names is None, it means that the scope is not authorized.
        if claim_names is not None:
            results.update(claim_names)

    _visit_handlers(handlers, visitor, 'scope', scopes)

    return results


def _collect_values(handlers, names, user, client, values):
    """ Get the values from the handlers of the requested claims. """

    results = {}

    def visitor(claim_name, func):
        data = {'user': user, 'client': client}
        data.update(values.get(claim_name) or {})
        claim_value = func(data)
        # If the claim_value is None, it means that the claim is not authorized.
        if claim_value is not None:
            # New values overwrite previous results
            results[claim_name] = claim_value

    _visit_handlers(handlers, visitor, 'claim', names)

    return results


def _validate_claim_request(claims, ignore_errors=False):
    """
    Validates a claim request section (`userinfo` or `id_token`) according
    to section 5.5 of the OpenID Connect specification:

    - http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

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

    results = []
    for handler in handlers:
        for suffix in suffixes:
            func = getattr(handler, '{}_{}'.format(preffix, suffix).lower(), None)
            if func:
                results.append(visitor(suffix, func))

    return results
