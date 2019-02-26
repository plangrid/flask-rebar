"""
    Messages
    ~~~~~~~~

    Helpers for generating messages that the API returns.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

body_validation_failed = "JSON body parameters are invalid."

empty_json_body = "Fields must be in JSON body."

internal_server_error = "Sorry, there was an internal error."

invalid_auth_token = "Invalid authentication."

invalid_json = "Failed to decode JSON body."

missing_auth_token = "No auth token provided."

query_string_validation_failed = "Query string parameters are invalid."

unsupported_content_type = (
    "Only payloads with 'content-type' 'application/json' are supported."
)

header_validation_failed = "Header parameters are invalid"


def required_field_missing(field_name):
    return "Required field missing: {}".format(field_name)


def required_field_empty(field_name):
    return "Value for required field cannot be None: {}".format(field_name)


def unsupported_fields(field_names):
    return "Unexpected field: {}".format(",".join(field_names))
