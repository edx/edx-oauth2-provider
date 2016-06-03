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
EMAIL_SCOPE = 1 << 2
COURSE_STAFF_SCOPE = 1 << 3
COURSE_INSTRUCTOR_SCOPE = 1 << 4
PERMISSIONS = 1 << 5

# Scope setting as required by django-oauth2-provider
# The default scope value is SCOPES[0][0], which in this case is zero.
# `django-oauth2-provider` considers a scope value of zero as empty,
# ignoring its name when requested.
SCOPES = (
    (DEFAULT_SCOPE, 'default'),
    (OPEN_ID_SCOPE, 'openid'),
    (PROFILE_SCOPE, 'profile'),
    (EMAIL_SCOPE, 'email'),
    (COURSE_STAFF_SCOPE, 'course_staff'),
    (COURSE_INSTRUCTOR_SCOPE, 'course_instructor'),
    (PERMISSIONS, 'permissions')
)

SCOPE_NAMES = [(name, name) for (value, name) in SCOPES]
SCOPE_NAME_DICT = dict([(name, value) for (value, name) in SCOPES])
SCOPE_VALUE_DICT = dict([(value, name) for (value, name) in SCOPES])


# OpenID Connect claim handlers

DEFAULT_ID_TOKEN_HANDLERS = (
    'oauth2_provider.oidc.handlers.BasicIDTokenHandler',
    'oauth2_provider.oidc.handlers.ProfileHandler',
    'oauth2_provider.oidc.handlers.EmailHandler',
)

DEFAULT_USERINFO_HANDLERS = (
    'oauth2_provider.oidc.handlers.BasicUserInfoHandler',
    'oauth2_provider.oidc.handlers.ProfileHandler',
    'oauth2_provider.oidc.handlers.EmailHandler',
)

ID_TOKEN_HANDLERS = getattr(settings, 'OAUTH_OIDC_ID_TOKEN_HANDLERS', DEFAULT_ID_TOKEN_HANDLERS)
USERINFO_HANDLERS = getattr(settings, 'OAUTH_OIDC_USERINFO_HANDLERS', DEFAULT_USERINFO_HANDLERS)


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

provider.oauth2.forms.SCOPES = SCOPES
provider.oauth2.forms.SCOPE_NAMES = SCOPE_NAMES

AUTHORIZED_CLIENTS_SESSION_KEY = getattr(settings, 'OAUTH_OIDC_AUTHORIZED_CLIENTS_SESSION_KEY', 'authorized_clients')
