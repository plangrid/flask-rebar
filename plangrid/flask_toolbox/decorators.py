from __future__ import unicode_literals

from functools import wraps

import bugsnag
from flask import request
from newrelic import agent as newrelic_agent
from werkzeug.security import safe_str_cmp

from plangrid.flask_toolbox import http_errors
from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.request_utils import verify_scope_or_403
from plangrid.flask_toolbox.toolbox_proxy import toolbox_proxy


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

        elif not safe_str_cmp(str(token), toolbox_proxy.auth_token):
            raise http_errors.Unauthorized(messages.invalid_auth_token)

        user_id = request.user_id

        if not user_id:
            raise http_errors.Unauthorized(messages.missing_user_id)

        bugsnag.configure_request(user={"id": user_id})
        newrelic_agent.add_custom_parameter('userId', user_id)

        return handler(*args, **kwargs)

    return wrapper


def scoped(required_scope):
    """
    Verifies that the request to the target endpoint has the proper scope.

    Scope is included as a space separated list in a header.

    :param str required_scope: The scope required to access this resource
    """
    def decorator(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            verify_scope_or_403(required_scope=required_scope)

            return handler(*args, **kwargs)

        return wrapper

    return decorator
