"""
Customized django-oauth2-provider views, aligned with the OpenID specification.

"""

import provider.oauth2.views
import provider.oauth2.forms
import provider.scope
from provider.oauth2.views import OAuthError
from provider.oauth2.views import Capture, Redirect  # pylint: disable=unused-import

from oauth2_provider import constants
from oauth2_provider.forms import PasswordGrantForm
from oauth2_provider.models import TrustedClient
from oauth2_provider.backends import PublicPasswordBackend
from oauth2_provider.oidc import make_id_token, encode_id_token
from oauth2_provider.forms import (AuthorizationRequestForm, AuthorizationForm,
                                   RefreshTokenGrantForm, AuthorizationCodeGrantForm)


# pylint: disable=abstract-method
class Authorize(provider.oauth2.views.Authorize):
    """
    edX customized authorization view:
      - Introduces trusted clients, which do not require user consent.
    """
    def get_request_form(self, client, data):
        return AuthorizationRequestForm(data, client=client)

    def get_authorization_form(self, request, client, data, client_data):
        # Check if the client is trusted. If so, bypass user
        # authorization by filling the data in the form.
        trusted = TrustedClient.objects.filter(client=client).exists()
        if trusted:
            scope_names = provider.scope.to_names(client_data['scope'])
            data = {'authorize': [u'Authorize'], 'scope': scope_names}

        form = AuthorizationForm(data)
        return form


# pylint: disable=abstract-method
class AccessTokenView(provider.oauth2.views.AccessTokenView):
    """
    edX customized access token view:
      - Allows usage of email as main identifier when requesting a
        password grant.
      - Return username along access token if requested in the scope.
      - Supports ID Tokens following the OpenID Connect specification.
    """

    # add custom authentication provider
    authentication = (provider.oauth2.views.AccessTokenView.authentication +
                      (PublicPasswordBackend, ))

    def get_authorization_code_grant(self, request, data, client):
        form = AuthorizationCodeGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data.get('grant')

    def get_refresh_token_grant(self, request, data, client):
        form = RefreshTokenGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data.get('refresh_token')

    def get_password_grant(self, _request, data, client):
        # Use customized form to allow use of user email during authentication
        form = PasswordGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data

    # pylint: disable=super-on-old-class
    def access_token_response_data(self, access_token):
        """
        Return `access_token` for OAuth2, and `id_token` for OpenID Connect
        according to the `access_token` scope.

        """
        response_data = super(AccessTokenView, self).access_token_response_data(access_token)

        # Add OpenID Connect `id_token` if requested
        if provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            # Add `id_token` according to OpenID specification
            id_token_data = self.id_token_data(access_token)
            response_data['id_token'] = self.encode_id_token(access_token, id_token_data)

        # Add other additional data
        extra_data = self.access_token_extra_response_data(access_token)

        # Update but don't override response_data values
        response_data = dict(extra_data.items() + response_data.items())

        return response_data

    def access_token_extra_response_data(self, access_token):
        """
        Return extra data that will be added to the token response.

        Useful for customizing the plain OAuth2 response.

        """
        data = {}

        if provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            # don't add anything if we are using OpenID Connect
            return data

        if provider.scope.check(constants.USERNAME_SCOPE, access_token.scope):
            data['preferred_username'] = access_token.user.username

        return data

    def id_token_data(self, access_token):
        """
        Return unencoded ID token unencoded data.

        """

        # A nonce is used to prevent replay attacks
        nonce = self.request.POST.get('nonce')

        return make_id_token(access_token, nonce)

    def encode_id_token(self, access_token, id_token_data):
        """
        Return encoded ID token.

        """
        # Encode the ID token using the `client_secret`.
        #
        # TODO: this is not ideal, since the `client_secret` is
        # transmitted over the wire in some authentication flows.
        # A better alternative is to use the public key of the issuer,
        # but that requires a bit more setup.
        secret = access_token.client.client_secret

        return encode_id_token(id_token_data, secret)
