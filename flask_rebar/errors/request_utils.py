import copy

import marshmallow
from flask import request
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest

from flask_rebar import messages, constants
from flask_rebar.errors import http_errors
from flask_rebar.request_utils import normalize_schema
from flask_rebar.validation import ObjectId


def _get_json_body_or_400():
    """
    Retrieves the JSON payload of the current request, throwing a 400 error
    if the request doesn't include a valid JSON payload.
    """
    if 'application/json' not in request.headers.get('content-type', ''):
        raise http_errors.BadRequest(messages.unsupported_content_type)

    if (not request.data) or (len(request.data) == 0):
        raise http_errors.BadRequest(messages.empty_json_body)

    try:
        body = request.get_json()
    except WerkzeugBadRequest:
        raise http_errors.BadRequest(messages.invalid_json)

    if not isinstance(body, list) and not isinstance(body, dict):
        # request.get_json_from_resp() treats strings as valid JSON, which is technically
        # true... but they're not valid objects. So let's throw an error on
        # primitive types.
        raise http_errors.BadRequest(messages.invalid_json)

    return body


def _format_marshmallow_errors_for_response_in_place(errs):
    """
    Reformats an error dictionary returned by marshmallow to an error
    dictionary we can send in a response.

    This transformation happens in place, so make sure to pass in a copy
    of the errors...
    """
    # These are errors on the entire schema, not a specific field
    # Let's rename these too something slightly less cryptic
    if '_schema' in errs:
        errs['_general'] = errs.pop('_schema')

    for field, value in errs.items():
        # In most cases we'll only have a single error for a field,
        # but marshmallow gives us a list regardless.
        # Let's try to reduce the complexity of the error response and convert
        # these lists to a single string.
        if isinstance(value, list) and len(value) == 1:
            errs[field] = value[0]
        elif isinstance(value, dict):
            # Recurse! Down the rabbit hole...
            _format_marshmallow_errors_for_response_in_place(value)


def raise_400_for_marshmallow_errors(errs, msg):
    """
    Throws a 400 error properly formatted from the given marshmallow errors.

    :param dict errs: Error dictionary as returned by marshmallow
    :param str msg: The overall message to use in the response.
    :raises: http_errors.BadRequest
    """
    if not errs:
        return

    copied = copy.deepcopy(errs)

    _format_marshmallow_errors_for_response_in_place(copied)

    additional_data = {'errors': copied}

    raise http_errors.BadRequest(
        msg=msg,
        additional_data=additional_data,
    )


def get_json_body_params_or_400(schema):
    """
    Retrieves the JSON body of a request, validating/loading the payload
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    body = _get_json_body_or_400()

    schema = normalize_schema(schema)

    json_body_params, errs = schema.load(data=body)

    if errs:
        raise_400_for_marshmallow_errors(
            errs=errs,
            msg=messages.body_validation_failed
        )

    return json_body_params


def get_query_string_params_or_400(schema):
    """
    Retrieves the query string of a request, validating/loading the parameters
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    query_multidict = request.args.copy()

    schema = normalize_schema(schema)

    # Deliberately use the request.args MultiDict in case a validator wants to
    # do something with several of the same query param (e.g. ?foo=1&foo=2), in
    # which case it will need the getlist method
    query_string_params, errs = schema.load(data=query_multidict)

    if errs:
        raise_400_for_marshmallow_errors(
            errs=errs,
            msg=messages.query_string_validation_failed
        )

    return query_string_params


def get_header_params_or_400(schema):
    schema = normalize_schema(schema)

    header_params, errs = schema.load(data=request.headers)

    if errs:
        raise_400_for_marshmallow_errors(
            errs=errs,
            msg=messages.header_validation_failed
        )

    return header_params


def get_user_id_from_header_or_400():
    """
    Retrieves the user ID from the header of a request, validating it as an
    ObjectID and raising a 400 error if it is missing or invalid.

    :rtype: str
    """
    user_id = request.headers.get(constants.HEADER_USER_ID)
    if not user_id:
        raise http_errors.BadRequest(msg=messages.missing_user_id)

    try:
        ObjectId().deserialize(value=user_id)
    except marshmallow.ValidationError:
        raise http_errors.BadRequest(msg=messages.invalid_user_id)

    return user_id
