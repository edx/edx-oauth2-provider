"""
URLs for testing.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import django.contrib.auth.views
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oauth2/', include('edx_oauth2_provider.urls', namespace='oauth2')),
    url(r'^accounts/login/$', django.contrib.auth.views.login,
        {'template_name': 'login.html'}),
    url(r'^accounts/logout/$', django.contrib.auth.views.logout,
        {'next_page': 'django.contrib.auth.views.login'}),
]
