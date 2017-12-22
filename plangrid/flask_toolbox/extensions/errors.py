from __future__ import unicode_literals

import sys

import bugsnag
from flask import current_app, jsonify
from newrelic import agent as newrelic_agent

from plangrid.flask_toolbox import http_errors, messages
from plangrid.flask_toolbox.extensions.extension import Extension


class Errors(Extension):
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

    def init_extension(self, app, config):
        @app.errorhandler(http_errors.HttpJsonError)
        def handle_http_error(error):
            return self._create_json_error_response(
                message=error.error_message,
                http_status_code=error.http_status_code,
                additional_data=error.additional_data
            )

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
