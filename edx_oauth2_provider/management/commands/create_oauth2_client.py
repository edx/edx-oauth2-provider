"""
Management command used to create an OAuth2 client in the database.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from provider.constants import CONFIDENTIAL, PUBLIC
from provider.oauth2.models import Client

from ...models import TrustedClient

ARG_STRING = '<url> <redirect_uri> <client_type: "confidential" | "public">'


class Command(BaseCommand):
    """
    create_oauth2_client command class
    """
    help = 'Create a new OAuth2 Client. Outputs a serialized representation of the newly-created Client.'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)

        # Required positional arguments.
        parser.add_argument(
            'url',
            help="Url."
        )
        parser.add_argument(
            'redirect_uri',
            help="Redirect URI."
        )
        parser.add_argument(
            'client_type',
            help="Client type."
        )

        # Optional options.
        parser.add_argument(
            '-u',
            '--username',
            help="Username of a user to associate with the Client."
        )
        parser.add_argument(
            '-n',
            '--client_name',
            help="String to assign as the Client name."
        )
        parser.add_argument(
            '-i',
            '--client_id',
            help="String to assign as the Client ID."
        )
        parser.add_argument(
            '-s',
            '--client_secret',
            help="String to assign as the Client secret. Should not be shared."
        )
        parser.add_argument(
            '-t',
            '--trusted',
            action='store_true',
            help="Designate the Client as trusted. Trusted Clients bypass the user consent "
                 "form typically displayed after validating the user's credentials."
        )
        parser.add_argument(
            '--logout_uri',
            help="Client logout URI. This value will be used for single sign out."
        )

    def handle(self, *args, **options):
        self._clean_required_args(options['url'], options['redirect_uri'], options['client_type'])
        self._parse_options(options)

        client_id = self.fields.get('client_id')
        trusted = self.fields.pop('trusted')

        # Check if client ID is already in use. If so, fetch existing Client and update fields.
        client_id_claimed = Client.objects.filter(client_id=client_id).exists()
        if client_id_claimed:
            client = Client.objects.get(client_id=client_id)

            for key, value in self.fields.items():
                setattr(client, key, value)

            client.save()
        else:
            client = Client.objects.create(**self.fields)

        if trusted:
            TrustedClient.objects.get_or_create(client=client)
        else:
            try:
                TrustedClient.objects.get(client=client).delete()
            except TrustedClient.DoesNotExist:
                pass

        serialized = json.dumps(client.serialize(), indent=4)
        self.stdout.write(serialized)

    def _clean_required_args(self, url, redirect_uri, client_type):
        """
        Validate and clean the command's arguments.

        Arguments:
            url (str): Client's application URL.
            redirect_uri (str): Client application's OAuth2 callback URI.
            client_type (str): Client's type, indicating whether the Client application
                is capable of maintaining the confidentiality of its credentials (e.g., running on a
                secure server) or is incapable of doing so (e.g., running in a browser).

        Raises:
            CommandError, if the URLs provided are invalid, or if the client type provided is invalid.
        """
        # Validate URLs
        for url_to_validate in (url, redirect_uri):
            try:
                URLValidator()(url_to_validate)
            except ValidationError:
                raise CommandError("URLs provided are invalid. Please provide valid application and redirect URLs.")

        # Validate and map client type to the appropriate django-oauth2-provider constant
        client_type = client_type.lower()
        client_type = {
            'confidential': CONFIDENTIAL,
            'public': PUBLIC
        }.get(client_type)

        if client_type is None:
            raise CommandError("Client type provided is invalid. Please use one of 'confidential' or 'public'.")

        self.fields = {  # pylint: disable=attribute-defined-outside-init
            'url': url,
            'redirect_uri': redirect_uri,
            'client_type': client_type,
        }

    def _parse_options(self, options):
        """Parse the command's options.

        Arguments:
            options (dict): Options with which the command was called.

        Raises:
            CommandError, if a user matching the provided username does not exist.
        """
        for key in ('username', 'client_name', 'client_id', 'client_secret', 'trusted', 'logout_uri'):
            value = options.get(key)
            if value is not None:
                self.fields[key] = value

        username = self.fields.pop('username', None)
        if username is not None:
            try:
                user_model = get_user_model()
                self.fields['user'] = user_model.objects.get(username=username)
            except user_model.DoesNotExist:
                raise CommandError("User matching the provided username does not exist.")

        # The keyword argument 'name' conflicts with that of `call_command()`. We instead
        # use 'client_name' up to this point, then swap it out for the expected field, 'name'.
        client_name = self.fields.pop('client_name', None)
        if client_name is not None:
            self.fields['name'] = client_name

        logout_uri = self.fields.get('logout_uri')

        if logout_uri:
            try:
                URLValidator()(logout_uri)
            except ValidationError:
                raise CommandError("The logout_uri is invalid.")
