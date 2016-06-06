"""
Customized django-oauth2-provider views, aligned with the OpenID specification.

"""
import json

from django.http import HttpResponse
from django.views.generic import View
import provider.oauth2.forms
from provider.oauth2.models import AccessToken
import provider.oauth2.views
from provider.oauth2.views import OAuthError, Capture, Redirect  # pylint: disable=unused-import
import provider.scope

from . import constants, oidc
from .backends import PublicPasswordBackend
from .forms import (
    PasswordGrantForm, AuthorizationRequestForm, AuthorizationForm, RefreshTokenGrantForm, AuthorizationCodeGrantForm
)
from .models import TrustedClient


# pylint: disable=abstract-method
class Authorize(provider.oauth2.views.Authorize):
    """
    edX customized authorization view:
      - Introduces trusted clients, which do not require user consent.
    """
    def get_request_form(self, client, data):
        return AuthorizationRequestForm(data, client=client)

    def get_authorization_form(self, _request, client, data, client_data):
        # Check if the client is trusted. If so, bypass user
        # authorization by filling the data in the form.
        trusted = TrustedClient.objects.filter(client=client).exists()
        if trusted:
            scope_names = provider.scope.to_names(client_data['scope'])
            data = {'authorize': [u'Authorize'], 'scope': scope_names}

        form = AuthorizationForm(data)
        return form

    def handle(self, request, post_data=None):
        response = super(Authorize, self).handle(request, post_data)

        if response.status_code < 400:
            # Store the ID of the client being used for authorization. We will use
            # this later to determine which clients to log out.
            client_id = request.session.get('oauth:client', {}).get('client_id')

            if client_id:
                client_ids = set(request.session.get(constants.AUTHORIZED_CLIENTS_SESSION_KEY, []))
                client_ids.add(client_id)
                request.session[constants.AUTHORIZED_CLIENTS_SESSION_KEY] = list(client_ids)

        return response


# pylint: disable=abstract-method
class AccessTokenView(provider.oauth2.views.AccessTokenView):
    """
    Customized OAuth2 access token view.

    Allows usage of email as main identifier when requesting a password grant.

    Support the ID Token endpoint following the OpenID Connect specification:

    - http://openid.net/specs/openid-connect-core-1_0.html#TokenEndpoint

    By default it returns all the claims available to the scope requested,
    and available to the claim handlers configured by `OAUTH_OIDC_ID_TOKEN_HANDLERS`

    """

    # Add custom authentication provider, to support email as username.
    authentication = (provider.oauth2.views.AccessTokenView.authentication +
                      (PublicPasswordBackend, ))

    # The following grant overrides make sure the view uses our customized forms.

    # pylint: disable=no-member
    def get_authorization_code_grant(self, _request, data, client):
        form = AuthorizationCodeGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data.get('grant')

    # pylint: disable=no-member
    def get_refresh_token_grant(self, _request, data, client):
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

    # pylint: disable=super-on-old-class
    def access_token_response_data(self, access_token):
        """
        Return `access_token` fields for OAuth2, and add `id_token` fields for
        OpenID Connect according to the `access_token` scope.

        """

        # Clear the scope for requests that do not use OpenID Connect.
        # Scopes for pure OAuth2 request are currently not supported.
        scope = constants.DEFAULT_SCOPE

        extra_data = {}

        # Add OpenID Connect `id_token` if requested.
        #
        # TODO: Unfourtunately because of how django-oauth2-provider implements
        # scopes, we cannot check if `openid` is the first scope to be
        # requested, as required by OpenID Connect specification.

        if provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            id_token = self.get_id_token(access_token)
            extra_data['id_token'] = self.encode_id_token(id_token)
            scope = provider.scope.to_int(*id_token.scopes)

        # Update the token scope, so it includes only authorized values.
        access_token.scope = scope
        access_token.save()

        # Get the main fields for OAuth2 response.
        response_data = super(AccessTokenView, self).access_token_response_data(access_token)

        # Add any additional fields if OpenID Connect is requested. The order of
        # the addition makes sures the OAuth2 values are not overrided.
        response_data = dict(extra_data.items() + response_data.items())

        return response_data

    def get_id_token(self, access_token):
        """ Return an ID token for the given Access Token. """

        claims_string = self.request.POST.get('claims')
        claims_request = json.loads(claims_string) if claims_string else {}

        # Use a nonce to prevent replay attacks.
        nonce = self.request.POST.get('nonce')

        return oidc.id_token(access_token, nonce, claims_request)

    def encode_id_token(self, id_token):
        """
        Return encoded ID token.

        """

        # Encode the ID token using the `client_secret`.
        #
        # TODO: Using the `client_secret` is not ideal, since it is transmitted
        # over the wire in some authentication flows.  A better alternative is
        # to use the public key of the issuer, which also allows the ID token to
        # be shared among clients. Doing so however adds some operational
        # costs. We should consider this for the future.

        secret = id_token.access_token.client.client_secret

        return id_token.encode(secret)


class ProtectedView(View):
    """
    Base View that checks for a valid OAuth2 access token.

    """

    # TODO: convert to a decorator.

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

    - http://openid.net/specs/openid-connect-basic-1_0.html#UserInfo

    By default it returns all the claims available to the `access_token` used, and available
    to the claim handlers configured by `OAUTH_OIDC_USERINFO_HANDLERS`

    In addition to the standard UserInfo response, this view also accepts custom scope
    and claims requests, using the scope and claims parameters as described in:

    http://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    http://openid.net/specs/openid-connect-core-1_0.html#ClaimsParameter

    Normally, such requests can only be done when requesting an ID Token. However, it is
    also convinient to support then in the UserInfo endpoint to do simply authorization checks.

    It ignores the top level claims request for `id_token`, in the claims
    request, using only the `userinfo` section.

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
        scope_request = scope_string.split() if scope_string else None

        claims_string = request.GET.get('claims')
        claims_request = json.loads(claims_string) if claims_string else None

        if not provider.scope.check(constants.OPEN_ID_SCOPE, access_token.scope):
            return self._bad_request('Missing openid scope.')

        try:
            claims = self.userinfo_claims(access_token, scope_request, claims_request)
        except ValueError, exception:
            return self._bad_request(str(exception))

        # TODO: Encode and sign responses if requested.

        response = JsonResponse(claims)

        return response

    def userinfo_claims(self, access_token, scope_request, claims_request):
        """ Return the claims for the requested parameters. """
        id_token = oidc.userinfo(access_token, scope_request, claims_request)
        return id_token.claims

    def _bad_request(self, msg):
        """ Return a 400 error with JSON content. """
        return JsonResponse({'error': msg}, status=400)


class JsonResponse(HttpResponse):
    """ Simple JSON Response wrapper. """
    def __init__(self, content, status=None, content_type='application/json'):
        super(JsonResponse, self).__init__(
            content=json.dumps(content),
            status=status,
            content_type=content_type,
        )
