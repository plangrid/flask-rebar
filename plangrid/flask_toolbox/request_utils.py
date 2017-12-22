from __future__ import unicode_literals

import marshmallow
from flask import jsonify


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


def marshal(data, schema):
    """
    Dumps an object with the given marshmallow.Schema.

    :raises: marshmallow.ValidationError if the given data fails validation
      of the schema.
    """
    schema = normalize_schema(schema)
    schema.strict = True
    return schema.dump(data).data


def normalize_schema(schema):
    """
    This allows for either an instance of a marshmallow.Schema or the class
    itself to be passed to functions.
    """
    if not isinstance(schema, marshmallow.Schema):
        return schema()
    else:
        return schema
