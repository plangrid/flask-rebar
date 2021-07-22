"""
    Messages
    ~~~~~~~~

    Helpers for generating messages that the API returns.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from collections import namedtuple
from enum import IntEnum


class ErrorCode(IntEnum):
    BODY_VALIDATION_FAILED = 1
    EMPTY_JSON_BODY = 2
    INTERNAL_SERVER_ERROR = 3
    INVALID_AUTH_TOKEN = 4
    INVALID_JSON = 5
    MISSING_AUTH_TOKEN = 6
    QUERY_STRING_VALIDATION_FAILED = 7
    UNSUPPORTED_CONTENT_TYPE = 8
    HEADER_VALIDATION_FAILED = 9
    REQUIRED_FIELD_MISSING = 10
    REQUIRED_FIELD_EMPTY = 11
    UNSUPPORTED_FIELDS = 12


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
