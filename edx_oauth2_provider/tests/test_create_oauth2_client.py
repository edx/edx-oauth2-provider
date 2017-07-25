"""
Tests of the create_oauth2_client management command.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import json
from itertools import product

import ddt
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils.six import StringIO
from provider.oauth2.models import Client

from ..models import TrustedClient

URL = 'https://www.example.com/'
REDIRECT_URI = 'https://www.example.com/complete/edx-oidc/'
CLIENT_TYPES = ('confidential', 'public')
USERNAME = 'username'


@ddt.ddt
class CreateOauth2ClientTests(TestCase):
    """
    Mgmt cmd test class.
    """
    def setUp(self):
        super(CreateOauth2ClientTests, self).setUp()
        user_model = get_user_model()
        self.user = user_model.objects.create(username=USERNAME)

    def _call_command(self, args, options=None):
        """Call the command, capturing its output."""
        if options is None:
            options = {}

        out = StringIO()
        options['stdout'] = out

        call_command('create_oauth2_client', *args, **options)

        return out

    def assert_client_created(self, args, options):
        """Call the command, verify that the Client was created, and validate the output."""
        out = self._call_command(args, options)
        client = Client.objects.get()

        # Verify command output
        serialized = json.dumps(client.serialize(), indent=4)
        self.assertIn(serialized, out.getvalue())

        # Verify Client associated with the correct user
        if options.get('username'):
            self.assertEqual(self.user, client.user)

        # Verify Client assigned the correct name
        client_name = options.get('client_name')
        if client_name:
            self.assertEqual(client_name, client.name)

        # Verify Client ID and secret overrides
        for attr in ('client_id', 'client_secret'):
            value = options.get(attr)
            if value is not None:
                self.assertEqual(value, getattr(client, attr))

        # Verify Client designated as trusted
        if options.get('trusted'):
            trusted_client = TrustedClient.objects.get()
            self.assertEqual(client, trusted_client.client)

    # Generate all valid argument and options combinations
    @ddt.data(*product(
        # Generate all valid argument combinations
        product(
            (URL,),
            (REDIRECT_URI,),
            (t for t in CLIENT_TYPES),
        ),
        # Generate all valid option combinations
        (dict(zip(('username', 'client_name', 'client_id', 'client_secret', 'trusted'), p)) for p in product(
            (USERNAME, None),
            ('name', None),
            ('id', None),
            ('secret', None),
            (True, False)
        ))
    ))
    @ddt.unpack
    def test_client_creation(self, args, options):
        """Verify that the command creates a Client when given valid arguments and options."""
        self.assert_client_created(args, options)

    @ddt.data(
        ((URL, REDIRECT_URI), 'too few arguments'),
        ((URL, REDIRECT_URI, CLIENT_TYPES[0], CLIENT_TYPES[1]), 'unrecognized arguments'),
    )
    @ddt.unpack
    def test_argument_cardinality(self, args, err_msg):
        """Verify that the command fails when given an incorrect number of arguments."""
        with self.assertRaises(CommandError) as exc:
            self._call_command(args, {})

        self.assertIn(err_msg, exc.exception.message)

    @ddt.data(
        ('invalid', REDIRECT_URI, CLIENT_TYPES[0]),
        (URL, 'invalid', CLIENT_TYPES[0]),
    )
    def test_url_validation(self, args):
        """Verify that the command fails when the provided URLs are invalid."""
        with self.assertRaises(CommandError) as exc:
            self._call_command(args)

        self.assertIn('URLs provided are invalid.', exc.exception.message)

    def test_client_type_validation(self):
        """Verify that the command fails when the provided client type is invalid."""
        with self.assertRaises(CommandError) as exc:
            self._call_command((URL, REDIRECT_URI, 'not_a_client_type'))

        self.assertIn('Client type provided is invalid.', exc.exception.message)

    def test_username_mismatch(self):
        """Verify that the command fails when the provided username is invalid."""
        with self.assertRaises(CommandError) as exc:
            self._call_command(
                (URL, REDIRECT_URI, CLIENT_TYPES[0]),
                options={'username': 'bad_username'}
            )

        self.assertIn('User matching the provided username does not exist.', exc.exception.message)

    def test_idempotency(self):
        """Verify that the command can be run repeatedly with the same client ID, without any ill effects."""
        args = [URL, REDIRECT_URI, CLIENT_TYPES[0]]
        options = {
            'username': None,
            'client_name': 'name',
            'client_id': 'id',
            'client_secret': 'secret',
            'trusted': True
        }

        self.assert_client_created(args, options)

        # Verify that the command is idempotent.
        self.assert_client_created(args, options)

        # Verify that attributes are updated if the command is run with the same client ID,
        # but with other options varying.
        options['client_secret'] = 'another-secret'
        self.assert_client_created(args, options)

        # Verify that the TrustedClient is deleted if the command is run with the same
        # client ID, but with the "--trusted" flag excluded.
        options['trusted'] = False
        self.assert_client_created(args, options)
        self.assertEqual(len(TrustedClient.objects.all()), 0)
