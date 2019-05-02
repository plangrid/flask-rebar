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
from flask_rebar.compat import MARSHMALLOW_V2


class CommaSeparatedList(fields.List):
    """
    A field class for Marshmallow; use this class when your list will be
    deserialized from a comma separated list of values.
    e.g. ?foo=bar,baz -> {'foo': ['bar', 'baz']}
    """

    def _deserialize(self, value, attr, data):
        items = value.split(",")
        return super(CommaSeparatedList, self)._deserialize(items, attr, data)

    def _serialize(self, value, attr, obj):
        items = super(CommaSeparatedList, self)._serialize(value, attr, obj)
        return ",".join([str(i) for i in items])


class QueryParamList(fields.List):
    """
    A field class for Marshmallow; use this class when your list will be
    deserialized from a query string containing the same param multiple
    times where each param is an item in the list.
    e.g. ?foo=bar&foo=baz -> {'foo': ['bar', 'baz']}
    """

    def _deserialize(self, value, attr, data):
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


class ActuallyRequireOnDumpMixin(object):
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


class DisallowExtraFieldsMixin(object):
    """
    By default, Marshmallow will silently ignore fields that aren't included in a schema
    when serializing/deserializing.

    This can be undesirable when doing request validation, as we want to notify a client
    when unrecognized fields are included.

    This is a `marshmallow.Schema` mixin that will throw an error when an object has
    unrecognized fields.
    """

    @validates_schema(pass_original=True)
    def disallow_extra_fields(self, processed_data, original_data):
        # If the input data isn't a dict just short-circuit and let the Marshmallow unmarshaller
        # raise an error.
        if not isinstance(original_data, dict):
            return

        input_fields = original_data.keys()
        expected_fields = list(self.fields) + [
            field.load_from
            for field in self.fields.values()
            if field.load_from is not None
        ]
        excluded_fields = self.exclude
        unsupported_fields = (
            set(input_fields) - set(expected_fields) - set(excluded_fields)
        )
        if len(unsupported_fields) > 0:
            raise ValidationError(
                message=messages.unsupported_fields(unsupported_fields)
            )


# Marshmallow version 3 starts "disallowing" extra fields by default
if MARSHMALLOW_V2:
    RequestSchema = type("RequestSchema", (DisallowExtraFieldsMixin, Schema), {})
else:
    RequestSchema = Schema


class ResponseSchema(ActuallyRequireOnDumpMixin, Schema):
    pass


class Error(Schema):
    message = fields.String(required=True)
    errors = fields.Dict(required=False)
