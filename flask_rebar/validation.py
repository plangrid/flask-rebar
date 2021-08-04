"""
    Validation
    ~~~~~~~~~~

    Helpful extensions for Marshmallow objects.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import post_dump
from marshmallow import validates_schema
from werkzeug.datastructures import MultiDict

from flask_rebar import messages


class CommaSeparatedList(fields.List):
    """
    A field class for Marshmallow; use this class when your list will be
    deserialized from a comma separated list of values.
    e.g. ?foo=bar,baz -> {'foo': ['bar', 'baz']}
    """

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, list):
            value = value.split(",")
        return super(CommaSeparatedList, self)._deserialize(value, attr, data)

    def _serialize(self, value, attr, obj, **kwargs):
        items = super(CommaSeparatedList, self)._serialize(value, attr, obj)
        return ",".join([str(i) for i in items])


class QueryParamList(fields.List):
    """
    A field class for Marshmallow; use this class when your list will be
    deserialized from a query string containing the same param multiple
    times where each param is an item in the list.
    e.g. ?foo=bar&foo=baz -> {'foo': ['bar', 'baz']}
    """

    def _deserialize(self, value, attr, data, **kwargs):
        # data is a MultiDict of query params, so pull out all of the items
        # with getlist instead of just the first
        if not isinstance(data, MultiDict):
            raise ValueError(
                "{} only deserializes {} instances".format(
                    self.__class__.__name__, MultiDict
                )
            )
        items = data.getlist(attr)
        return super(QueryParamList, self)._deserialize(items, attr, data)


class RequireOnDumpMixin(object):
    """
    By default, Marshmallow only raises an error when required fields are missing
    when `marshmallow.Schema.load` is called.

    This is a `marshmallow.Schema` mixin that will throw an error when an object is
    missing required fields when `marshmallow.Schema.dump` is called, or if one of
    the required fields fails a validator.
    """

    @post_dump(pass_many=True)
    def require_output_fields(self, data, many):
        errors = self.validate(data)
        if errors:
            raise ValidationError(errors, data=data)
        return data


RequestSchema = Schema


class ResponseSchema(RequireOnDumpMixin, Schema):
    pass


class Error(Schema):
    message = fields.String(required=True)
    errors = fields.Dict(required=False)
