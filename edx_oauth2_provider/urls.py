"""
OAuth2 provider urls
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from provider.oauth2.views import AccessTokenDetailView

from .views import Authorize, Redirect, Capture, AccessTokenView, UserInfoView


urlpatterns = patterns(
    '',
    url('^authorize/?$', login_required(Capture.as_view()), name='capture'),
    url('^authorize/confirm/?$', login_required(Authorize.as_view()), name='authorize'),
    url('^redirect/?$', login_required(Redirect.as_view()), name='redirect'),
    url('^access_token/?$', csrf_exempt(AccessTokenView.as_view()), name='access_token'),
    url('^access_token/(?P<token>[\w]+)/$', csrf_exempt(AccessTokenDetailView.as_view()), name='access_token_detail'),
    url('^user_info/?$', csrf_exempt(UserInfoView.as_view()), name='user_info'),
)
