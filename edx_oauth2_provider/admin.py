"""
OAuth2 provider Django admin interface
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib import admin

from .models import TrustedClient


class TrustedClientAdmin(admin.ModelAdmin):
    "Django admin configuration for `TrustedClient` model"
    list_display = ('client',)


admin.site.register(TrustedClient, TrustedClientAdmin)
