from __future__ import unicode_literals

from functools import wraps

import bugsnag
from flask import g
from flask import request
from newrelic import agent as newrelic_agent
from werkzeug.security import safe_str_cmp

from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.errors import http_errors


def authenticated(handler):
    """
    Verifies that the request to the target endpoint is authenticated.

    Authentication currently happens via a shared token.
    A user id is also required to be sent in via the header to give an
    authorization context for the handler.
    """
    @wraps(handler)
    def wrapper(*args, **kwargs):
        token = request.auth_token

        if not token:
            raise http_errors.Unauthorized(messages.missing_auth_token)

        elif not safe_str_cmp(str(token), g.toolbox_auth_token):
            raise http_errors.Unauthorized(messages.invalid_auth_token)

        user_id = request.user_id

        if not user_id:
            raise http_errors.Unauthorized(messages.missing_user_id)

        bugsnag.configure_request(user={"id": user_id})
        newrelic_agent.add_custom_parameter('userId', user_id)

        return handler(*args, **kwargs)

    return wrapper
