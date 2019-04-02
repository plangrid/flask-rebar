"""
    Header API Key Authenticator
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Authenticator for API key passed in header.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from flask import request, g
from werkzeug.security import safe_str_cmp

from flask_rebar import errors, messages
from flask_rebar.authenticators.base import Authenticator


def get_authenticated_app_name():
    return g.authenticated_app_name


class HeaderApiKeyAuthenticator(Authenticator):
    """
    Authenticates based on a small set of shared secrets, passed via a header.

    This allows multiple client applications to be registered with their own
    keys.
    This also allows multiple keys to be registered for a single client
    application.

    :param str header:
        The header where clients where client applications must include
        their secret.
    :param str name:
        A name for this authenticator. This should be unique across
        authenticators.
    """

    # This authenticator allows multiple applications to have different keys.
    # This is the default name, if someone doesn't need about this feature.
    DEFAULT_APP_NAME = "default"

    def __init__(self, header, name="sharedSecret"):
        self.header = header
        self.keys = {}
        self.name = name

    @property
    def authenticated_app_name(self):
        return get_authenticated_app_name()

    def register_key(self, key, app_name=DEFAULT_APP_NAME):
        """
        Register a client application's shared secret.

        :param str app_name:
            Name for the application. Since an application can have multiple
            shared secrets, this does not need to be unique.
        :param str key:
            The shared secret.
        """
        self.keys[key] = app_name

    def authenticate(self):
        if self.header not in request.headers:
            raise errors.Unauthorized(messages.missing_auth_token)

        token = request.headers[self.header]

        for key, app_name in self.keys.items():
            if safe_str_cmp(str(token), key):
                g.authenticated_app_name = app_name
                break
        else:
            raise errors.Unauthorized(messages.invalid_auth_token)
