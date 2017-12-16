from __future__ import unicode_literals

import copy
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import marshmallow
from flask import request
from flask import jsonify

from plangrid.flask_toolbox import (
    toolbox_proxy,
    http_errors,
    messages
)
from plangrid.flask_toolbox.validation import ObjectId


def scope_app(app, required_scope):
    """
    Extends an application (or blueprint) to only accept requests that
    have the proper scope set in the headers.

    :param flask.Flask|flask.Blueprint app:

    :param str required_scope:
      The extension will verify that all requests have this scope in the headers
    """

    @app.before_request
    def verify_scope():
        verify_scope_or_403(required_scope=required_scope)


def _make_url(resource_path, query_params):
    """
    Constructs a full URL for the application.

    :param str resource_path: e.g. /path/to/resource
    :param dict query_params: e.g. {'skip': 0, 'limit': 100}
    :return: e.g. https://io.plangrid.com/path/to/resource?skip=0&limit=100
    :rtype: str
    """
    url_params = urlencode(
        [
            (param, value)
            # sorted so testing is more reliable
            for param, value in sorted(query_params.items())
            if value is not None
        ]
    )

    return '{}{}?{}'.format(toolbox_proxy.base_url, resource_path, url_params)


def paginated_response(data, total_count, additional_data=None, status_code=200):
    """
    Constructs a flask.Response for paginated endpoint.

    :param list data: The current page of data to return to the client
    :param int total_count: The total amount of resources matching the query
    :param dict additional_data: Any additional data to attach to the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    resp = {
        'data': data,
        'total_count': total_count,
        'next_page_url': None
    }

    query_params = request.args.to_dict()

    skip = int(query_params.get('skip', 0))
    limit = int(query_params.get('limit', toolbox_proxy.pagination_limit_max))

    if skip + limit < total_count:
        query_params['skip'] = skip + limit
        query_params['limit'] = limit
        resp['next_page_url'] = _make_url(
            resource_path=request.path,
            query_params=query_params
        )

    if additional_data:
        resp.update(additional_data)

    return response(data=resp, status_code=status_code)


def response(data, status_code=200):
    """
    Constructs a flask.Response.

    :param dict data: The JSON body of the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    resp = jsonify(data)
    resp.status_code = status_code
    return resp


def list_response(data, additional_data, status_code=200):
    """
    Constructs a flask.Response for an endpoint that returns a list.

    :param list data:
    :param dict additional_data: Any additional data to attach to the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    resp = {'data': data}
    if additional_data:
        resp.update(additional_data)
    return response(data=resp, status_code=status_code)


def _get_json_body_or_400():
    """
    Retrieves the JSON payload of the current request, throwing a 400 error
    if the request doesn't include a valid JSON payload.
    """
    if 'application/json' not in request.headers.get('content-type', ''):
        raise http_errors.BadRequest(messages.unsupported_content_type)

    if (not request.data) or (len(request.data) == 0):
        raise http_errors.BadRequest(messages.empty_json_body)

    # JSON decoding errors will be handled in ToolboxRequest.on_json_loading_failed
    body = request.get_json()

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


def _normalize_schema(schema):
    """
    This allows for either an instance of a marshmallow.Schema or the class
    itself to be passed to functions.
    """
    if not isinstance(schema, marshmallow.Schema):
        return schema()
    else:
        return schema


def get_json_body_params_or_400(schema):
    """
    Retrieves the JSON body of a request, validating/loading the payload
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    body = _get_json_body_or_400()

    schema = _normalize_schema(schema)

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

    schema = _normalize_schema(schema)

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
    schema = _normalize_schema(schema)

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
    user_id = request.user_id
    if not user_id:
        raise http_errors.BadRequest(msg=messages.missing_user_id)

    try:
        ObjectId().deserialize(value=user_id)
    except marshmallow.ValidationError:
        raise http_errors.BadRequest(msg=messages.invalid_user_id)

    return user_id


def verify_scope_or_403(required_scope):
    """
    Verifies that the given scope is included in the request headers. If it
    isn't, this will raise a 403 error.

    :param str required_scope:
    :raises: https_errors.Forbidden
    """
    if required_scope not in request.scopes:
        raise http_errors.Forbidden(messages.missing_required_scope)


def marshal(data, schema):
    """
    Dumps an object with the given marshmallow.Schema.

    :raises: marshmallow.ValidationError if the given data fails validation
      of the schema.
    """
    schema = _normalize_schema(schema)
    schema.strict = True
    return schema.dump(data).data
