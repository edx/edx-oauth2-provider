edX OAuth2 Provider
===================
OAuth2 provider for edX Platform.

`oauth2_provider` is a Django application used for authentication and authorization in the edx-platform. The
authentication mechanism is aligned with the OpenID Connect specification, supporting some of it basic features.

Usage
-----

The OAuth2 clients must be registered to obtain their `client_id` and `client_secret`. The registration can be done using the
`/admin` web interface by adding new entries to the OAuth2 Clients table.

Apart from the two basic OAuth2 client types (_public_ and _confidential_), this provider as a notion of a _trusted_
client. Trusted clients do not require user consent for accessing user resources, and will not show up the approval
page during the sign-in process. To make a client trusted after it has been created, add it to the OAuth2-provider
`TrustedModel` tables using the `/admin` web interface.

Open ID Connect
---------------

Currently, only the OpenID Connect `profile` scope is supported. Following the specification, OpenID Connect request
should use the `openid` scope.

The `id_token` is signed (HMAC) using the `client_secret` with the SHA-256 algorithm.

The value of the setting `OAUTH_OIDC_ISSUER` MUST be set to the issuer URL. According to the OpenID connect to
specification, it should use the `https` scheme, host and optionally the port number and path.

The `id_token` expiration, which defaults to 30 seconds, can be overriden by setting `OAUTH_ID_TOKEN_EXPIRATION` to a
different value.


Testing
-------

        $ ./manage.py test


How to Contribute
-----------------
Contributions are very welcome, but for legal reasons, you must submit a signed
[individual contributor's agreement](http://code.edx.org/individual-contributor-agreement.pdf)
before we can accept your contribution. See our
[CONTRIBUTING](https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst)
file for more information -- it also contains guidelines for how to maintain
high code quality, which will make your contribution more likely to be accepted.


Reporting Security Issues
-------------------------
Please do not report security issues in public. Please email security@edx.org.


Mailing List and IRC Channel
----------------------------

You can discuss this code on the [edx-code Google Group](https://groups.google.com/forum/#!forum/edx-code) or in the
`edx-code` IRC channel on Freenode.
