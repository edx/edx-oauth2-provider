import provider.constants
import provider.scope
import provider.oauth2.forms

# Use bit-shifting so that scopes can be easily combined and checked.
DEFAULT_SCOPE = 0
USERNAME_SCOPE = 1

# Define scopes. Required by django-oauth2-provider.
# The default scope value is OAUTH_SCOPES[0][0]
SCOPES = (
    (DEFAULT_SCOPE, 'default'),
    (USERNAME_SCOPE, 'preferred_username'),
)

SCOPE_NAMES = [(name, name) for (value, name) in SCOPES]
SCOPE_NAME_DICT = dict([(name, value) for (value, name) in SCOPES])
SCOPE_VALUE_DICT = dict([(value, name) for (value, name) in SCOPES])


# Override django-oauth2-provider scopes

provider.constants.SCOPES = SCOPES
provider.constants.DEFAULT_SCOPES = SCOPES

provider.scope.SCOPES = SCOPES
provider.scope.SCOPE_NAMES = SCOPE_NAMES
provider.scope.SCOPE_NAME_DICT = SCOPE_NAME_DICT
provider.scope.SCOPE_VALUE_DICT = SCOPE_VALUE_DICT
