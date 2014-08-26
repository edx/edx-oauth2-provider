# pylint: disable=missing-docstring

from django.test import TestCase

from provider.constants import CONFIDENTIAL

from oauth2_provider import constants
from oauth2_provider.tests import data
from oauth2_provider.tests.factories import UserFactory, ClientFactory, AccessTokenFactory


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory.create(
            username=data.USERNAME,
            email=data.EMAIL,
            password=data.PASSWORD,
        )

        self.auth_client = ClientFactory.create(
            client_id=data.CLIENT_ID,
            client_secret=data.CLIENT_SECRET,
            client_type=CONFIDENTIAL
        )

        self.access_token = AccessTokenFactory.create(
            user=self.user,
            client=self.auth_client,
            scope=constants.OPEN_ID_SCOPE
        )
