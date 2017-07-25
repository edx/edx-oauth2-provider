"""
OAuth2 provider urls
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from provider.oauth2.views import AccessTokenDetailView

from .views import AccessTokenView, Authorize, Capture, Redirect, UserInfoView

urlpatterns = [
    url(r'^authorize/?$', login_required(Capture.as_view()), name='capture'),
    url(r'^authorize/confirm/?$', login_required(Authorize.as_view()), name='authorize'),
    url(r'^redirect/?$', login_required(Redirect.as_view()), name='redirect'),
    url(r'^access_token/?$', csrf_exempt(AccessTokenView.as_view()), name='access_token'),
    url(r'^access_token/(?P<token>[\w]+)/$', csrf_exempt(AccessTokenDetailView.as_view()), name='access_token_detail'),
    url(r'^user_info/?$', csrf_exempt(UserInfoView.as_view()), name='user_info'),
]
