"""
OAuth2 provider customized `django-oauth2-provider` forms.

"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

import provider.oauth2.forms
import provider.constants
from provider.forms import OAuthValidationError
from provider.oauth2.forms import ScopeChoiceField
from provider.oauth2.models import Client

from .constants import SCOPE_NAMES


# The following forms override the scope field to use the SCOPE_NAMES
# defined for this provider. Otherwise it will use the default values from
# the django-oauth2-provider package.

# pylint: disable=missing-docstring,no-member

class AuthorizationRequestForm(provider.oauth2.forms.AuthorizationRequestForm):
    def __init__(self, *args, **kwargs):
        super(AuthorizationRequestForm, self).__init__(*args, **kwargs)
        self.fields['scope'] = ScopeChoiceField(choices=SCOPE_NAMES, required=False)


class AuthorizationForm(provider.oauth2.forms.AuthorizationForm):
    def __init__(self, *args, **kwargs):
        super(AuthorizationForm, self).__init__(*args, **kwargs)
        self.fields['scope'] = ScopeChoiceField(choices=SCOPE_NAMES, required=False)


class RefreshTokenGrantForm(provider.oauth2.forms.RefreshTokenGrantForm):
    def __init__(self, *args, **kwargs):
        super(RefreshTokenGrantForm, self).__init__(*args, **kwargs)
        self.fields['scope'] = ScopeChoiceField(choices=SCOPE_NAMES, required=False)


class AuthorizationCodeGrantForm(provider.oauth2.forms.AuthorizationCodeGrantForm):
    def __init__(self, *args, **kwargs):
        super(AuthorizationCodeGrantForm, self).__init__(*args, **kwargs)
        self.fields['scope'] = ScopeChoiceField(choices=SCOPE_NAMES, required=False)


# pylint: enable=missing-docstring,no-member

# The forms in this module are required to use email as a secondary
# identifier when authenticating via OAuth2, since the specification
# only uses the `username` parameter.
#
# TODO: An alternative, simpler, approach is to write a backend that
# like `django.contrib.auth.backends.ModelBackend` and add it to
# `AUTHENTICATION_BACKENDS` in the Django settings.


class PasswordGrantForm(provider.oauth2.forms.PasswordGrantForm):
    """
    Forms that validates the user email to be used as secondary user
    identifier during authentication.

    """

    def clean(self):
        data = self.cleaned_data  # pylint: disable=no-member
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)

        # If the username was not found try the user using username as
        # the email address. It is valid because the edx-platform has
        # a unique constraint placed on the email field.
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if (
            user is None
            # TODO This is a temporary workaround while the is_active field on the
            # user is coupled with whether or not the user has verified ownership
            # of their claimed email address.  Once is_active is decoupled from
            # verified_email, we can uncomment the following line.
            # or not user.is_active
        ):
            raise OAuthValidationError({'error': 'invalid_grant'})

        data['user'] = user
        return data


class PublicPasswordGrantForm(PasswordGrantForm,
                              provider.oauth2.forms.PublicPasswordGrantForm):
    """
    Form wrapper to ensure the the customized PasswordGrantForm is used
    during client authentication.

    """
    def clean(self):
        data = super(PublicPasswordGrantForm, self).clean()

        try:
            client = Client.objects.get(client_id=data.get('client_id'))
        except Client.DoesNotExist:
            raise OAuthValidationError({'error': 'invalid_client'})

        if client.client_type != provider.constants.PUBLIC:
            raise OAuthValidationError({'error': 'invalid_client'})

        data['client'] = client
        return data
