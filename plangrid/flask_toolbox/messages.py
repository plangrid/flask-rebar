invalid_json = 'Failed to decode JSON body.'

internal_server_error = 'Internal Server Error'

empty_json_body = 'Fields must be in JSON body.'

unsupported_content_type = "Only payloads with 'content-type' 'application/json' are supported."

body_validation_failed = 'JSON body parameters are invalid.'

query_string_validation_failed = 'Query string parameters are invalid.'

missing_auth_token = 'No auth token provided.'

invalid_auth_token = 'Invalid authentication.'

missing_user_id = 'No user_id provided.'

health_check_response = "I'm doing OK, thanks for asking."

invalid_skip_value = 'Skip must be 0 or positive integer.'

invalid_limit_value = 'Limit must be a positive integer.'

def limit_over_max(max_limit):
    return 'Maximum limit is {}'.format(max_limit)

invalid_object_id = 'Not a valid ObjectID.'

invalid_uuid = 'Not a valid UUID.'

def required_field_missing(field_name):
    return "Required field missing: {}".format(field_name)

def required_field_empty(field_name):
    return "Value for required field cannot be None: {}".format(field_name)

def unsupported_fields(field_names):
    return 'Unexpected field: {}'.format(','.join(field_names))
