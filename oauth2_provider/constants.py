"""
OAuth2 and OpenID Connect settings

"""

from django.conf import settings

import provider.constants
import provider.scope
import provider.oauth2.forms


# REQUIRED Issuer Identifider (the `iss` field in the `id_token`)
OAUTH_OIDC_ISSUER = settings.OAUTH_OIDC_ISSUER

# OAUTH/2 OpenID Connect scopes

# Use bit-shifting so that scopes can be easily combined and checked.
DEFAULT_SCOPE = 0
OPEN_ID_SCOPE = 1 << 0
PROFILE_SCOPE = 1 << 1
USERNAME_SCOPE = 1 << 2
EMAIL_SCOPE = 1 << 3

# All scopes as required by django-oauth2-provider
# The default scope value is SCOPES[0][0]
SCOPES = (
    (DEFAULT_SCOPE, 'default'),
    (OPEN_ID_SCOPE, 'openid'),
    (PROFILE_SCOPE, 'profile'),
    (USERNAME_SCOPE, 'username'),  # Only used for OAuth, not OIDC.
    (USERNAME_SCOPE, 'preferred_username'),  # Alias of username
    (EMAIL_SCOPE, 'email'),
)

SCOPE_NAMES = [(name, name) for (value, name) in SCOPES]
SCOPE_NAME_DICT = dict([(name, value) for (value, name) in SCOPES])
SCOPE_VALUE_DICT = dict([(value, name) for (value, name) in SCOPES])


# Override django-oauth2-provider scopes (OAUTH_SCOPES)
#
# `provider.scopes` values are loaded from Django settings. However,
# we don't want to rely on customizable settings, and instead use the
# set of defaults above. One problem, is that in many places
# `django-oauth2-provider` creates module globals with the values from
# settings, making them hard to override.
#
# TODO: This solution is bit ugly, but viable for now. A better fix is
# to make SCOPES be lazy evaluated at the django-oauth2-provider level
# using django.utils.functional.lazy

provider.constants.SCOPES = SCOPES
provider.constants.DEFAULT_SCOPES = SCOPES

provider.scope.SCOPES = SCOPES
provider.scope.SCOPE_NAMES = SCOPE_NAMES
provider.scope.SCOPE_NAME_DICT = SCOPE_NAME_DICT
provider.scope.SCOPE_VALUE_DICT = SCOPE_VALUE_DICT
