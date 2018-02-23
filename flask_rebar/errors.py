"""
    Errors
    ~~~~~~

    Exceptions that get transformed to HTTP error responses.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals


class HttpJsonError(Exception):
    """
    Abstract base class for exceptions that will be cause and transformed
    into an appropriate HTTP error response with a JSON body.

    These can be raised at any time during the handling of a request,
    and the Rebar extension will handling catching it and transforming it.

    This class itself shouldn't be used. Instead, use one of the subclasses.

    :param str msg:
        A human readable message to be included in the JSON error response
    :param dict additional_data:
        Dictionary of additional keys and values to be set in the JSON body.
        Note that these keys and values are added to the root object of the
        response, not nested under "additional_data".
    """
    default_message = None
    http_status_code = None

    def __init__(self, msg=None, additional_data=None):
        self.error_message = msg or self.default_message
        self.additional_data = additional_data
        super(HttpJsonError, self).__init__(self.error_message)


class BadRequest(HttpJsonError):
    http_status_code, default_message = 400, 'Bad Request'


class Unauthorized(HttpJsonError):
    http_status_code, default_message = 401, 'Unauthorized'


class PaymentRequired(HttpJsonError):
    http_status_code, default_message = 402, 'Payment Required'


class Forbidden(HttpJsonError):
    http_status_code, default_message = 403, 'Forbidden'


class NotFound(HttpJsonError):
    http_status_code, default_message = 404, "Not Found"


class MethodNotAllowed(HttpJsonError):
    http_status_code, default_message = 405, "Method Not Allowed"


class NotAcceptable(HttpJsonError):
    http_status_code, default_message = 406, "Not Acceptable"


class ProxyAuthenticationRequired(HttpJsonError):
    http_status_code, default_message = 407, "Proxy Authentication Required"


class RequestTimeout(HttpJsonError):
    http_status_code, default_message = 408, "Request Timeout"


class Conflict(HttpJsonError):
    http_status_code, default_message = 409, 'Conflict'


class Gone(HttpJsonError):
    http_status_code, default_message = 410, 'Gone'


class LengthRequired(HttpJsonError):
    http_status_code, default_message = 411, 'Length Required'


class PreconditionFailed(HttpJsonError):
    http_status_code, default_message = 412, 'Precondition Failed'


class RequestEntityTooLarge(HttpJsonError):
    http_status_code, default_message = 413, 'Request Entity Too Large'


class RequestUriTooLong(HttpJsonError):
    http_status_code, default_message = 414, 'Request URI Too Long'


class UnsupportedMediaType(HttpJsonError):
    http_status_code, default_message = 415, 'Unsupported Media Type'


class RequestedRangeNotSatisfiable(HttpJsonError):
    http_status_code, default_message = 416, 'Requested Range Not Satisfiable'


class ExpectationFailed(HttpJsonError):
    http_status_code, default_message = 417, 'Expectation Failed'


class UnprocessableEntity(HttpJsonError):
    http_status_code, default_message = 422, 'Unprocessable Entity'


class InternalError(HttpJsonError):
    http_status_code, default_message = 500, "Internal Server Error"


class NotImplemented(HttpJsonError):
    http_status_code, default_message = 501, 'Not Implemented'


class BadGateway(HttpJsonError):
    http_status_code, default_message = 502, 'Bad Gateway'


class ServiceUnavailable(HttpJsonError):
    http_status_code, default_message = 503, 'Service Unavailable'


class GatewayTimeout(HttpJsonError):
    http_status_code, default_message = 504, 'Gateway Timeout'
