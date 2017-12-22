from __future__ import unicode_literals

import os
import uuid

from flask import Request

from plangrid.flask_toolbox import http_errors, messages
from plangrid.flask_toolbox.extensions.healthcheck import Healthcheck
from plangrid.flask_toolbox.extensions.healthcheck import HEALTHCHECK_ENDPOINT as _HEALTHCHECK_ENDPOINT
from plangrid.flask_toolbox.extensions.errors import Errors
from plangrid.flask_toolbox.extensions.bugsnag import Bugsnag
from plangrid.flask_toolbox.extensions.url_converters import UrlConverters


DEFAULT_PAGINATION_LIMIT_MAX = 100
HEADER_AUTH_TOKEN = 'X-PG-Auth'
HEADER_USER_ID = 'X-PG-UserId'
HEADER_REQUEST_ID = 'X-PG-RequestId'
HEADER_SCOPES = 'X-PG-Scopes'
HEADER_APPLICATION_ID = 'X-PG-AppId'

# Alias this for backwards compatibility reasons
HEALTHCHECK_ENDPOINT = _HEALTHCHECK_ENDPOINT


class ToolboxRequest(Request):
    """Lightly wraps flask.Request to getters for PlanGrid specific headers."""
    @property
    def user_id(self):
        return self.headers.get(HEADER_USER_ID)

    @property
    def request_id(self):
        return self.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))

    @property
    def auth_token(self):
        return self.headers.get(HEADER_AUTH_TOKEN)

    @property
    def application_id(self):
        return self.headers.get(HEADER_APPLICATION_ID)

    @property
    def scopes(self):
        scopes_string = self.headers.get(HEADER_SCOPES, '').strip()
        if scopes_string:
            scopes_split = [
                s.strip()
                for s in scopes_string.split(' ')
                if s
            ]
            return set(scopes_split)
        else:
            return set()

    def on_json_loading_failed(self, e):
        raise http_errors.BadRequest(messages.invalid_json)


class Toolbox(object):
    """
    Extends a Flask application to become a PlanGrid style REST API.

    :param flask.Flask app:


    Configuration parameters
    ------------------------

    These are retrieved in the following priority order:
    1) If the parameter is passed in on instantiation, that value get's first
       priority,
    2) Otherwise, the application's config object is inspected for the
       parameter.
    3) If the application's config doesn't have it, the environment is
       inspected for the variable.

    :param str base_url: TOOLBOX_BASE_URL
      When generating URLs in responses, this will be used
      as the base of the url (i.e. the schema and hostname).
      For example: 'https://io.plangrid.com'

    :param str auth_token: TOOLBOX_AUTH_TOKEN
      This token is used as a secret shared key with authenticating incoming
      requests (i.e., if a handler is decorated as @authenticated, incoming
      requests will be inspected for the X-PG-Auth header, and that header
      must match this token).

    :param int pagination_limit_max: TOOLBOX_PAGINATION_LIMIT_MAX
      Limit request parameters will default to this value.

    :param str bugsnag_api_key: BUGSNAG_API_KEY
      The API key for the bugsnag integration.

    :param str bugsnag_release_stage: BUGSNAG_RELEASE_STAGE
      Notifications to bugsnag will be namespaced under this release stage.
      Usually this is the "stack" that the application is running in...
      e.g. "dev", "test", or "prod"
    """
    def __init__(
            self,
            app=None,
            base_url=None,
            auth_token=None,
            pagination_limit_max=None,
            bugsnag_api_key=None,
            bugsnag_release_stage=None
    ):
        self.app = app
        self.base_url = base_url
        self.auth_token = auth_token
        self.pagination_limit_max = pagination_limit_max
        self.bugsnag_api_key = bugsnag_api_key
        self.bugsnag_release_stage = bugsnag_release_stage

        if app is not None:
            self.init_app(app)

    @staticmethod
    def _get_config(app, env_var_name, default=None):
        """
        Gets a config variable from either the app.config or the environment
        """
        return app.config.get(env_var_name, os.getenv(env_var_name, default))

    def init_app(self, app):
        self.base_url = (
            self.base_url
            if self.base_url is not None
            else self._get_config(app, 'TOOLBOX_BASE_URL')
        )
        self.auth_token = (
            self.auth_token
            if self.auth_token is not None
            else self._get_config(app, 'TOOLBOX_AUTH_TOKEN')
        )
        self.pagination_limit_max = int(
            self.pagination_limit_max
            if self.pagination_limit_max is not None
            else self._get_config(app, 'TOOLBOX_PAGINATION_LIMIT_MAX',
                                  default=DEFAULT_PAGINATION_LIMIT_MAX)
        )
        self.bugsnag_api_key = (
            self.bugsnag_api_key
            if self.bugsnag_api_key is not None
            else self._get_config(app, 'BUGSNAG_API_KEY')
        )
        self.bugsnag_release_stage = (
            self.bugsnag_release_stage
            if self.bugsnag_release_stage is not None
            else self._get_config(app, 'BUGSNAG_RELEASE_STAGE',
                                  default='production')
        )

        Bugsnag(
            app=app,
            config={
                'BUGSNAG_RELEASE_STAGE': self.bugsnag_release_stage,
                'BUGSNAG_API_KEY': self.bugsnag_api_key
            }
        )
        Errors(app=app)
        Healthcheck(app=app)
        UrlConverters(app=app)

        # Set the flask.request proxy to our extended type
        app.request_class = ToolboxRequest

        # Add a reference to this Toolbox instance in the app context
        app.app_ctx_globals_class.toolbox = self
