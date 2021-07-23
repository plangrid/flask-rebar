"""
    Messages
    ~~~~~~~~

    Helpers for generating messages that the API returns.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from collections import namedtuple


# machine-friendly equivalents of associated human-friendly messages
class ErrorCode:
    BODY_VALIDATION_FAILED = "body_validation_failed"
    EMPTY_JSON_BODY = "empty_json_body"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    INVALID_AUTH_TOKEN = "invalid_auth_token"
    INVALID_JSON = "invalid_json"
    MISSING_AUTH_TOKEN = "missing_auth_token"
    QUERY_STRING_VALIDATION_FAILED = "query_string_validation_failed"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    HEADER_VALIDATION_FAILED = "header_validation_failed"
    REQUIRED_FIELD_MISSING = "required_fields_missing"
    REQUIRED_FIELD_EMPTY = "required_field_empty"
    UNSUPPORTED_FIELDS = "unsupported_fields"


ErrorMessage = namedtuple("ErrorMessage", "message, rebar_error_code")


body_validation_failed = ErrorMessage(
    "JSON body parameters are invalid.", ErrorCode.BODY_VALIDATION_FAILED
)

empty_json_body = ErrorMessage(
    "Fields must be in JSON body.", ErrorCode.EMPTY_JSON_BODY
)

internal_server_error = ErrorMessage(
    "Sorry, there was an internal error.", ErrorCode.INTERNAL_SERVER_ERROR
)

invalid_auth_token = ErrorMessage(
    "Invalid authentication.", ErrorCode.INVALID_AUTH_TOKEN
)

invalid_json = ErrorMessage("Failed to decode JSON body.", ErrorCode.INVALID_JSON)

missing_auth_token = ErrorMessage(
    "No auth token provided.", ErrorCode.MISSING_AUTH_TOKEN
)

query_string_validation_failed = ErrorMessage(
    "Query string parameters are invalid.", ErrorCode.QUERY_STRING_VALIDATION_FAILED
)

unsupported_content_type = ErrorMessage(
    "Only payloads with 'content-type' 'application/json' are supported.",
    ErrorCode.UNSUPPORTED_CONTENT_TYPE,
)

header_validation_failed = ErrorMessage(
    "Header parameters are invalid", ErrorCode.HEADER_VALIDATION_FAILED
)


def required_field_missing(field_name):
    return ErrorMessage(
        "Required field missing: {}".format(field_name),
        ErrorCode.REQUIRED_FIELD_MISSING,
    )


def required_field_empty(field_name):
    return ErrorMessage(
        "Value for required field cannot be None: {}".format(field_name),
        ErrorCode.REQUIRED_FIELD_EMPTY,
    )


def unsupported_fields(field_names):
    return ErrorMessage(
        "Unexpected field: {}".format(",".join(field_names)),
        ErrorCode.UNSUPPORTED_FIELDS,
    )
