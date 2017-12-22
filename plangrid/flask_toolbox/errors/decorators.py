from functools import wraps

from plangrid.flask_toolbox.errors.request_utils import verify_scope_or_403


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
