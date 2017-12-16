from __future__ import unicode_literals

import os
import sys
import uuid

import bugsnag
import bugsnag.flask
from flask import Request, current_app, jsonify
from newrelic import agent as newrelic_agent

from plangrid.flask_toolbox import http_errors, messages
from plangrid.flask_toolbox.converters import UUIDStringConverter

DEFAULT_PAGINATION_LIMIT_MAX = 100
HEADER_AUTH_TOKEN = 'X-PG-Auth'
HEADER_USER_ID = 'X-PG-UserId'
HEADER_REQUEST_ID = 'X-PG-RequestId'
HEADER_SCOPES = 'X-PG-Scopes'
HEADER_APPLICATION_ID = 'X-PG-AppId'
HEALTHCHECK_ENDPOINT = 'health'


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

        self._register_custom_error_handler(app)
        self._register_werkzeug_error_handler(app)
        self._register_healthcheck(app)
        if self.bugsnag_api_key:
            self._configure_bugsnag(app)
        self._register_custom_converters(app)

        # Set the flask.request proxy to our extended type
        app.request_class = ToolboxRequest

        # Add a reference to this Toolbox instance in the app context
        app.app_ctx_globals_class.toolbox = self

    def _create_json_error_response(
            self,
            message,
            http_status_code,
            error_code=None,
            additional_data=None
    ):
        """
        Compiles a response object for an error.

        :param str message:
        :param int http_status_code:
        :param error_code:
          An optional, application-specific error code to add to the response.
        :param additional_data:
          Additional JSON data to attach to the response.
        :rtype: flask.Response
        """
        body = {'message': message}
        if error_code:
            body['error_code'] = error_code
        if additional_data:
            body.update(additional_data)
        resp = jsonify(body)
        resp.status_code = http_status_code
        return resp

    def _register_custom_error_handler(self, app):
        """Registers an error handler for our flask_toolbox.http_errors."""
        @app.errorhandler(http_errors.HttpJsonError)
        def handle_http_error(error):
            return self._create_json_error_response(
                message=error.error_message,
                http_status_code=error.http_status_code,
                additional_data=error.additional_data
            )

    def _register_werkzeug_error_handler(self, app):
        """Registers handlers to change built-in Flask errors to JSON errors."""
        @app.errorhandler(404)
        @app.errorhandler(405)
        def handle_werkzeug_http_error(error):
            return self._create_json_error_response(
                message=error.description,
                http_status_code=error.code
            )

        @app.errorhandler(Exception)
        def handle_werkzeug_http_error(error):
            exc_info = sys.exc_info()
            current_app.log_exception(exc_info=exc_info)
            bugsnag.notify(error)
            newrelic_agent.record_exception(*exc_info)
            return self._create_json_error_response(
                message=messages.internal_server_error,
                http_status_code=500
            )

    def _register_healthcheck(self, app):
        """Adds a /health endpoint to the application."""
        @app.route('/health', endpoint=HEALTHCHECK_ENDPOINT)
        def handle_healthcheck():
            return jsonify({'message': messages.health_check_response})

    def _configure_bugsnag(self, app):
        """Configures flask to forward uncaught exceptions to Bugsnag."""
        bugsnag.configure(
            api_key=self.bugsnag_api_key,
            release_stage=self.bugsnag_release_stage
        )
        bugsnag.flask.handle_exceptions(app)

    def _register_custom_converters(self, app):
        app.url_map.converters['uuid_string'] = UUIDStringConverter
