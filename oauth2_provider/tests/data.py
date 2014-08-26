from provider.constants import CONFIDENTIAL

ISSUER = 'https://example.com/'

USERNAME = 'some_username'
EMAIL = 'test@example.com'
PASSWORD = 'some_password'

CLIENT_ID = 'some_client_id'
CLIENT_SECRET = 'some_client_secret'

# Data to generate login tests. Missing fields default to the values
# in the module variables above. 'success' defaults to False.
# 'client_secret' is not used unless specified.
CUSTOM_PASSWORD_GRANT_TEST_DATA = [
    {
        'success': True
    },
    {
        'username': EMAIL,
        'success': True
    },
    {
        'password': PASSWORD + '_bad',
    },
    {
        'username': USERNAME + '_bad',
    },
    {
        'client_id': CLIENT_ID + '_bad'
    },
    {
        'username': EMAIL,
        'password': PASSWORD + '_bad',
    },
    {
        'client_secret': CLIENT_SECRET,
        'success': True
    },
    {
        'client_type': CONFIDENTIAL,
        'client_secret': CLIENT_SECRET,
        'success': True
    },
    {
        'client_secret': CLIENT_SECRET + '_bad',
        'success': True  # public clients should ignore the client_secret field
    },
    {
        'client_type': CONFIDENTIAL,
        'client_secret': CLIENT_SECRET + '_bad',
    },
]
