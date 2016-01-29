import json
from optparse import make_option

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from provider.constants import CONFIDENTIAL, PUBLIC
from provider.oauth2.models import Client

from ...models import TrustedClient


try:
    from django.contrib.auth import get_user_model
except ImportError:  # Django <1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

ARG_STRING = '<url> <redirect_uri> <client_type: "confidential" | "public">'


class Command(BaseCommand):
    help = 'Create a new OAuth2 Client. Outputs a serialized representation of the newly-created Client.'
    args = ARG_STRING
    fields = None

    option_list = BaseCommand.option_list + (
        make_option(
            '-u',
            '--username',
            action='store',
            type='string',
            dest='username',
            help="Username of a user to associate with the Client."
        ),
        make_option(
            '-n',
            '--client_name',
            action='store',
            type='string',
            dest='client_name',
            help="String to assign as the Client name."
        ),
        make_option(
            '-i',
            '--client_id',
            action='store',
            type='string',
            dest='client_id',
            help="String to assign as the Client ID."
        ),
        make_option(
            '-s',
            '--client_secret',
            action='store',
            type='string',
            dest='client_secret',
            help="String to assign as the Client secret. Should not be shared."
        ),
        make_option(
            '-t',
            '--trusted',
            action='store_true',
            dest='trusted',
            default=False,
            help="Designate the Client as trusted. Trusted Clients bypass the user consent "
                 "form typically displayed after validating the user's credentials."
        ),
    )

    def handle(self, *args, **options):
        self._clean_args(args)
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

    def _clean_args(self, args):
        """Validate and clean the command's arguments.

        These arguments must include the Client application's URL, the Client application's
        OAuth2 callback URL, and the Client's type, indicating whether the Client application
        is capable of maintaining the confidentiality of its credentials (e.g., running on a
        secure server) or is incapable of doing so (e.g., running in a browser).

        Arguments:
            args (tuple): Arguments with which the command was called.

        Raises:
            CommandError, if the number of arguments provided is invalid, if the URLs provided
                are invalid, or if the client type provided is invalid.
        """
        if len(args) != 3:
            raise CommandError(
                "Number of arguments provided is invalid. "
                "This command requires the following arguments: {}.".format(ARG_STRING)
            )

        url, redirect_uri, client_type = args

        # Validate URLs
        for u in (url, redirect_uri):
            try:
                URLValidator()(u)
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

        self.fields = {
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
        for key in ('username', 'client_name', 'client_id', 'client_secret', 'trusted'):
            value = options.get(key)
            if value is not None:
                self.fields[key] = value

        username = self.fields.pop('username', None)
        if username is not None:
            try:
                self.fields['user'] = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError("User matching the provided username does not exist.")

        # The keyword argument 'name' conflicts with that of `call_command()`. We instead
        # use 'client_name' up to this point, then swap it out for the expected field, 'name'.
        client_name = self.fields.pop('client_name', None)
        if client_name is not None:
            self.fields['name'] = client_name
