"""
    Request Utilities
    ~~~~~~~~~~~~~~~~

    Utilities for request handlers.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals

import copy

import marshmallow
from flask import Response
from flask import jsonify
from flask import request
from werkzeug.datastructures import Headers
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest

from flask_rebar import compat
from flask_rebar import errors
from flask_rebar import messages
from flask_rebar.utils.defaults import USE_DEFAULT


class HeadersProxy(compat.Mapping):
    """
    Marshmallow expects objects being deserialized to be instances of `Mapping`.

    This wraps werkzeug's `EnvironHeaders` to ensure that they're an instance of `Mapping`.

    :param werkzeug.datastructures.EnvironHeaders headers:
    """

    __slots__ = ("headers",)

    def __init__(self, headers):
        self.headers = headers

    def __len__(self):
        return len(self.headers)

    def __iter__(self):
        # EnvironHeaders.__iter__ yields tuples of (key, value).
        # We want to mimic a dict and yield keys.
        return iter(self.headers.keys())

    def __contains__(self, item):
        return item in self.headers

    def __getitem__(self, key):
        return self.headers[key]


def response(data, status_code=200, headers=None, mimetype=None):
    """
    Constructs a flask.jsonify response.

    :param dict data: The JSON body of the response
    :param int status_code: HTTP status code to use in the response
    :param dict headers: Additional headers to attach to the response
    :param str mimetype: Default Content-Type response header
    :rtype: flask.Response
    """
    resp = jsonify(data) if data is not None else Response()

    resp.status_code = status_code

    if mimetype:
        headers.update({"Content-Type": mimetype})
    if headers:
        response_headers = dict(resp.headers)
        response_headers.update(headers)
        resp.headers = Headers(response_headers)

    return resp


def marshal(data, schema):
    """
    Dumps an object with the given marshmallow.Schema.

    :raises: marshmallow.ValidationError if the given data fails validation
      of the schema.
    """
    schema = normalize_schema(schema)
    return compat.dump(schema=schema, data=data)


def normalize_schema(schema):
    """
    This allows for either an instance of a marshmallow.Schema or the class
    itself to be passed to functions.
    """
    if schema not in (None, USE_DEFAULT) and not isinstance(schema, marshmallow.Schema):
        schema = schema()
    return schema


def raise_400_for_marshmallow_errors(errs, msg):
    """
    Throws a 400 error properly formatted from the given marshmallow errors.

    :param dict errs: Error dictionary as returned by marshmallow
    :param str msg: The overall message to use in the response.
    :raises: errors.BadRequest
    """
    if not errs:
        return

    copied = copy.deepcopy(errs)

    _format_marshmallow_errors_for_response_in_place(copied)

    additional_data = {"errors": copied}

    raise errors.BadRequest(msg=msg, additional_data=additional_data)


def get_json_body_params_or_400(schema):
    """
    Retrieves the JSON body of a request, validating/loading the payload
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    body = _get_json_body_or_400()

    return _get_data_or_400(
        schema=schema, data=body, message=messages.body_validation_failed
    )


def get_query_string_params_or_400(schema):
    """
    Retrieves the query string of a request, validating/loading the parameters
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    # Use the request.args MultiDict in case a validator wants to
    # do something with several of the same query param (e.g. ?foo=1&foo=2), in
    # which case it will need the getlist method
    query_multidict = request.args.copy()

    return _get_data_or_400(
        schema=schema,
        data=query_multidict,
        message=messages.query_string_validation_failed,
    )


def get_header_params_or_400(schema):
    schema = compat.exclude_unknown_fields(schema)
    return _get_data_or_400(
        schema=schema,
        data=HeadersProxy(request.headers),
        message=messages.header_validation_failed,
    )


def _get_data_or_400(schema, data, message):
    schema = normalize_schema(schema)

    try:
        return compat.load(schema=schema, data=data)

    except marshmallow.ValidationError as e:
        raise_400_for_marshmallow_errors(errs=e.messages, msg=message)


def _get_json_body_or_400():
    """
    Retrieves the JSON payload of the current request, throwing a 400 error
    if the request doesn't include a valid JSON payload.
    """
    if "application/json" not in request.headers.get("content-type", ""):
        raise errors.BadRequest(messages.unsupported_content_type)

    if (not request.data) or (len(request.data) == 0):
        raise errors.BadRequest(messages.empty_json_body)

    try:
        body = request.get_json()
    except WerkzeugBadRequest:
        raise errors.BadRequest(messages.invalid_json)

    if not isinstance(body, list) and not isinstance(body, dict):
        # request.get_json_from_resp() treats strings as valid JSON, which is technically
        # true... but they're not valid objects. So let's throw an error on
        # primitive types.
        raise errors.BadRequest(messages.invalid_json)

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
    if "_schema" in errs:
        errs["_general"] = errs.pop("_schema")

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
