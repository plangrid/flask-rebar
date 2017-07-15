body_validation_failed = 'JSON body parameters are invalid.'

empty_json_body = 'Fields must be in JSON body.'

health_check_response = "I'm doing OK, thanks for asking."

internal_server_error = "Sorry, PlanGrid's system had an error and the team has been notified. If this happens again, please contact developers@plangrid.com."

invalid_auth_token = 'Invalid authentication.'

invalid_json = 'Failed to decode JSON body.'

invalid_limit_value = 'Limit must be a positive integer.'

invalid_object_id = 'Not a valid ObjectID.'

invalid_skip_value = 'Skip must be 0 or positive integer.'

invalid_user_id = 'Invalid user ID.'

invalid_uuid = 'Not a valid UUID.'

missing_auth_token = 'No auth token provided.'

missing_required_scope = 'Missing the required scope to access resource.'

missing_user_id = 'No user ID provided.'

query_string_validation_failed = 'Query string parameters are invalid.'

unsupported_content_type = "Only payloads with 'content-type' 'application/json' are supported."


def limit_over_max(max_limit):
    return 'Maximum limit is {}'.format(max_limit)


def required_field_empty(field_name):
    return "Value for required field cannot be None: {}".format(field_name)


def required_field_missing(field_name):
    return "Required field missing: {}".format(field_name)


def unsupported_fields(field_names):
    return 'Unexpected field: {}'.format(','.join(field_names))
