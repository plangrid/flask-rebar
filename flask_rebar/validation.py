import marshmallow
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow import post_dump
from marshmallow import validates_schema

from flask_rebar import messages


class CommaSeparatedList(fields.List):
    def _deserialize(self, value, attr, data):
        items = value.split(',')
        return super(CommaSeparatedList, self)._deserialize(items, attr, data)

    def _serialize(self, value, attr, obj):
        items = super(CommaSeparatedList, self)._serialize(value, attr, obj)
        return ','.join([str(i) for i in items])


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
        items = data.getlist(attr)
        return super(QueryParamList, self)._deserialize(items, attr, data)


class ActuallyRequireOnDumpMixin(object):
    @post_dump()
    def require_output_fields(self, data):
        for field_name in self.fields:
            field = self.fields[field_name]
            if field.required:
                if field_name not in data:
                    raise ValidationError(messages.required_field_missing(field_name))
                elif field.allow_none is False and data[field_name] is None:
                    raise ValidationError(messages.required_field_empty(field_name))


class DisallowExtraFieldsMixin(object):
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
        unsupported_fields = set(input_fields) - set(expected_fields) - set(excluded_fields)
        if len(unsupported_fields) > 0:
            raise ValidationError(message=messages.unsupported_fields(unsupported_fields))


class RequestSchema(DisallowExtraFieldsMixin, marshmallow.Schema):
    pass


class ResponseSchema(ActuallyRequireOnDumpMixin, marshmallow.Schema):
    pass


class Error(marshmallow.Schema):
    message = fields.String(required=True)
    errors = fields.Dict(required=False)
