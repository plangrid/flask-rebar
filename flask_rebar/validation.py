"""
    Validation
    ~~~~~~~~~~

    Helpful extensions for Marshmallow objects.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from collections import Mapping, namedtuple

from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import post_dump
from marshmallow import validates_schema
from werkzeug.datastructures import MultiDict

from flask_rebar import messages

FilterResult = namedtuple("FilterResult", "loadable, dump_only")


def filter_dump_only(schema, data):
    """
    Return a filtered copy of data in which any items matching a "dump_only" field are removed
    :param schema: Instance of a Schema class
    :param data: Dict or collection of dicts with data
    :return: Union[FilterResult, list[FilterResult]]
    """
    # Note as of marshmallow 3.13.0, Schema.dump_only is NOT populated if fields are declared as dump_only inline,
    # so we'll calculate "dump_only" ourselves.  ref: https://github.com/marshmallow-code/marshmallow/issues/1857
    dump_only_fields = schema.dump_fields.keys() - schema.load_fields.keys()
    if isinstance(data, Mapping):
        filter_result = FilterResult(
            dict(),  # we may need to do some recursion so we'll build these in following loop
            {
                k: v for k, v in data.items() if k in dump_only_fields
            },  # dump_only won't require further recursion
        )
        for k, v in {
            k: v for k, v in data.items() if k not in dump_only_fields
        }.items():  # "loadable" fields
            field = schema.fields[k]
            # see if we have a nested schema (using either Nested(many=True) or List(Nested()
            field_schema = (
                field.schema
                if isinstance(field, fields.Nested)
                else field.inner.schema
                if isinstance(field, fields.List)
                and isinstance(field.inner, fields.Nested)
                else None
            )
            if field_schema is not None:
                field_filtered = filter_dump_only(field_schema, v)
                filter_result.loadable[k] = field_filtered.loadable
                filter_result.dump_only[k] = field_filtered.dump_only
            else:
                filter_result.loadable[k] = v

        return filter_result
    elif isinstance(data, list):
        processed_items = [filter_dump_only(schema, item) for item in data]
        return FilterResult(
            [item.loadable for item in processed_items],
            [item.dump_only for item in processed_items],
        )

    else:
        # I am not aware of any case where we should get something other than a Mapping or list, but just in case
        # we can raise a hopefully helpful error if there's some weird Schema that can cause that, so we know
        # we need to update this and patch rebar ;)
        raise TypeError(f"filter_dump_only doesn't understand data type {type(data)}")


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
        filtered = filter_dump_only(self, data)
        errors = self.validate(filtered.loadable)
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


RequestSchema = Schema


class ResponseSchema(RequireOnDumpMixin, Schema):
    pass


class Error(Schema):
    message = fields.String(required=True)
    errors = fields.Dict(required=False)
