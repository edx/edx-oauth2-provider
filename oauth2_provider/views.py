"""
Customized django-oauth2-provider views, aligned with the OpenID specification.

"""
import json

from django.http import HttpResponse
from django.views.generic import View

import provider.oauth2.views
import provider.oauth2.forms
import provider.scope
from provider.oauth2.models import AccessToken
from provider.oauth2.views import OAuthError
from provider.oauth2.views import Capture, Redirect  # pylint: disable=unused-import

from oauth2_provider import constants
from oauth2_provider.forms import PasswordGrantForm
from oauth2_provider.models import TrustedClient
from oauth2_provider.backends import PublicPasswordBackend
from oauth2_provider.oidc import id_token_claims, userinfo_claims, encode_claims, authorized_scopes
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

    # Add custom authentication provider.
    authentication = (provider.oauth2.views.AccessTokenView.authentication +
                      (PublicPasswordBackend, ))

    # The following grant overrides make sure the view uses our customized forms.

    # pylint: disable=no-member
    def get_authorization_code_grant(self, request, data, client):
        form = AuthorizationCodeGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data.get('grant')

    # pylint: disable=no-member
    def get_refresh_token_grant(self, request, data, client):
        form = RefreshTokenGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data.get('refresh_token')

    # pylint: disable=no-member
    def get_password_grant(self, _request, data, client):
        # Use customized form to allow use of user email during authentication.
        form = PasswordGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data

    def create_access_token(self, request, user, scope, client):
        """
        Create access token. If the `openid` scope is requested, it check
        all the scopes are authorized for the corresponding user and
        OAuth2 client.

        """
        if provider.scope.check(constants.OPEN_ID_SCOPE, scope):
            # If using OpenID Connect, get only authorized scopes.
            scope_names = provider.scope.to_names(scope)
            scope_names = authorized_scopes(scope_names, user, client)
            scope = provider.scope.to_int(*scope_names)

        access_token = super(AccessTokenView, self).create_access_token(request, user, scope, client)
        return access_token

    # pylint: disable=super-on-old-class
    def access_token_response_data(self, access_token):
        """
        Return `access_token` for OAuth2, and `id_token` for OpenID Connect
        according to the `access_token` scope.

        """
        response_data = super(AccessTokenView, self).access_token_response_data(access_token)

        # Add OpenID Connect `id_token` if requested.
        if provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            id_token_data = self.id_token_data(access_token)
            response_data['id_token'] = self.encode_id_token(access_token, id_token_data)

        extra_data = self.access_token_extra_response_data(access_token)

        # Update but don't override response_data values.
        response_data = dict(extra_data.items() + response_data.items())

        return response_data

    def access_token_extra_response_data(self, access_token):
        """
        Return extra data that will be added to the token response.

        Useful for customizing the plain OAuth2 response.

        """
        data = {}

        if provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            # Don't add anything if we are using OpenID Connect
            return data

        return data

    def id_token_data(self, access_token):
        """
        Return unencoded ID token unencoded data.

        """

        # A nonce is used to prevent replay attacks
        nonce = self.request.POST.get('nonce')

        # Claims request parameter if any
        claims_string = self.request.POST.get('claims')
        claims_request = json.loads(claims_string) if claims_string else None

        # By default this grants all the scopes that are requested.
        return id_token_claims(access_token, nonce, claims_request)

    def encode_id_token(self, access_token, id_token_data):
        """
        Return encoded ID token.

        """
        # Encode the ID token using the `client_secret`.
        #
        # TODO: Using the `client_secret` is not ideal, since
        # it is transmitted over the wire in some authentication
        # flows.  A better alternative is to use the public key of the
        # issuer, which also allows the ID token to be shared among
        # clients. Doing so however adds some operational costs. We
        # should consider this for the future.
        secret = access_token.client.client_secret

        return encode_claims(id_token_data, secret)


class ProtectedView(View):
    """
    Base View that checks for a valid OAuth2 access token.

    """

    # TODO: convert to a decorator

    access_token = None
    user = None

    def dispatch(self, request, *args, **kwargs):
        error_msg = None

        # Get the header value
        token = request.META.get('HTTP_AUTHORIZATION', '')

        # Trim the Bearer portion
        token = token.replace('Bearer ', '')

        if token:
            # Verify token exists and is valid
            access_token = AccessToken.objects.filter(token=token)
            if access_token:
                access_token = access_token[0]
            else:
                access_token = None

            if access_token is None or access_token.get_expire_delta() <= 0:
                error_msg = 'invalid_token'
            else:
                self.access_token = access_token
                self.user = access_token.user
        else:
            # Return an error response if no token supplied
            error_msg = 'access_denied'

        if error_msg:
            return JsonResponse({'error': error_msg}, status=401)

        return super(ProtectedView, self).dispatch(request, *args, **kwargs)


class UserInfoView(ProtectedView):
    """
    Implementation of the Basic OpenID Connect UserInfo endpoint as described in:

    http://openid.net/specs/openid-connect-basic-1_0.html#UserInfo

    By default it returns all the claims available to the `access_token` used, and available
    to the claim handlers configured by `OAUTH_OIDC_USERINFO_HANDLERS`

    In addition to the standard UserInfo response, this view also accepts custom scope
    and claims requests, using the scope and claims parameters as described in:

    http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Normally, such requests can only be done when requesting an ID Token. However, it is
    also convinient to support then in the UserInfo endpoint to do simply authorization checks.

    Since this is the UserInfo Endpoint, it ignores the top level claims request for `id_token`,
    using only the `userinfo` field.

    All requests to this endpoint must include at least the 'openid' scope.

    Currently only supports GET request, and does not sign any responses.

    """

    def get(self, request, *_args, **_kwargs):
        """
        Respond to a UserInfo request.

        Two optional query parameters are accepted, scope and claims.
        See the references above for more details.

        """

        access_token = self.access_token

        scope_string = request.GET.get('scope')
        scope_names = scope_string.split() if scope_string else None

        claims_string = request.GET.get('claims')
        claims_request = json.loads(claims_string) if claims_string else None

        if not provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            return self._bad_request('Missing openid scope.')

        try:
            data = self.userinfo_data(access_token, scope_names, claims_request)
        except ValueError, exception:
            return self._bad_request(str(exception))

        response = JsonResponse(data)

        return response

    def userinfo_data(self, access_token, scope_names, claims_request):
        """ Return a dict representing the user data to be returned by the view. """
        return userinfo_claims(access_token, scope_names, claims_request)

    def _bad_request(self, msg):
        """ Return a 400 error with JSON content. """
        return JsonResponse({'error': msg}, status=400)


class JsonResponse(HttpResponse):
    """ Simple JSON Response """
    def __init__(self, content, status=None, content_type='application/json'):
        super(JsonResponse, self).__init__(
            content=json.dumps(content),
            status=status,
            content_type=content_type,
        )
