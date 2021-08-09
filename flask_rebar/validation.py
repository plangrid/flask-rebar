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
    Return a filtered copy of data in which any items matching a "dump_only" field are separated
    :param schema: Instance of a Schema class
    :param data: Dict or collection of dicts with data
    :return: Union[FilterResult, list[FilterResult]]
    """
    # Note as of marshmallow 3.13.0, Schema.dump_only is NOT populated if fields are declared as dump_only inline,
    # so we'll calculate "dump_only" ourselves.  ref: https://github.com/marshmallow-code/marshmallow/issues/1857
    dump_only_fields = schema.dump_fields.keys() - schema.load_fields.keys()
    if isinstance(data, Mapping):
        dump_only = dict()
        non_dump_only = dict()
        # get our dump_only fields directly, and candidates for loadable:
        for k, v in data.items():
            if k in dump_only_fields:
                dump_only[k] = v
            else:
                non_dump_only[k] = v

        # construct loadable (a subset of non_dump_only, with recursive filter of nested dump_only fields)
        loadable = dict()
        for k, v in non_dump_only.items():
            field = schema.fields[k]
            # see if we have a nested schema (using either Nested(many=True) or List(Nested())
            field_schema = None
            if isinstance(field, fields.Nested):
                field_schema = field.schema
            elif isinstance(field, fields.List) and isinstance(
                field.inner, fields.Nested
            ):
                field_schema = field.inner.schema
            if field_schema is None:
                loadable[k] = v
            else:
                field_filtered = filter_dump_only(field_schema, v)
                loadable[k] = field_filtered.loadable
                dump_only[k] = field_filtered.dump_only
        return FilterResult(loadable=loadable, dump_only=dump_only)
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
    DEPRECATED AND MAY BE REMOVED IN VERSION 3.0
    In previous versions, this mixin was used to force validation on dump. As of 2.0.1, that
    validation is now fully encapsulated in compat.dump, with the presence of this mixin as one of
    the triggers.
    """

    pass


RequestSchema = Schema


class ResponseSchema(RequireOnDumpMixin, Schema):
    pass


class Error(Schema):
    message = fields.String(required=True)
    errors = fields.Dict(required=False)
