"""
    Marshmallow to Swagger Conversion
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities for converting Marshmallow objects to their
    corresponding Swagger representation.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals

import copy
import inspect
import logging
import sys
from collections import namedtuple

import marshmallow as m
from marshmallow.validate import Range
from marshmallow.validate import OneOf
from marshmallow.validate import Length
from marshmallow.validate import Validator

from flask_rebar import compat
from flask_rebar.validation import QueryParamList
from flask_rebar.validation import CommaSeparatedList
from flask_rebar.validation import DisallowExtraFieldsMixin
from flask_rebar.swagger_generation import swagger_words as sw


# Special value to signify that a JSONSchema field should be left unset
class UNSET(object):
    pass


# We'll use this to mark methods as JSONSchema attribute setters
_method_marker = "__sets_jsonschema_attr__"

# Holds attributes that we can pass around in these recursive
# calls to converters. Bit messy, but :shrug:
_Context = namedtuple(
    "_Context",
    [
        # This will hold a reference to a convert method that can be used
        # to make recursive calls
        "convert",
        # Only really using this for validators at the moment. It will hold the
        # JSONSchema object that's been converter so far, so that the validator
        # can be converted based on the type of the schema.
        "memo",
        # The current schema being converted.
        "schema",
        # The major version of OpenAPI being converter for
        "openapi_version",
    ],
)


class UnregisteredType(Exception):
    pass


def _normalize_validate(validate):
    """
    Coerces the validate attribute on a Marshmallow field to a consistent type.

    The validate attribute on a Marshmallow field can either be a single
    Validator or a collection of Validators.

    :param Validator|list[Validator] validate:
    :rtype: list[Validator]
    """
    if callable(validate):
        return [validate]
    else:
        return validate


def get_swagger_title(obj):
    """
    Gets a title for the given object. This title will be used
    as a name/key for the object in swagger.

    :param obj:
    :rtype: str
    """
    if hasattr(obj, "__swagger_title__"):
        return obj.__swagger_title__
    elif hasattr(obj, "__name__"):
        return obj.__name__
    else:
        return obj.__class__.__name__


def sets_swagger_attr(attr):
    """
    Decorates a `MarshmallowConverter` method, marking it as an JSONSchema
    attribute setter.

    Example usage::

        class Converter(MarshmallowConverter):
            MARSHMALLOW_TYPE = String()

            @sets_swagger_attr('type')
            def get_type(obj, context):
                return 'string'

    This converter receives instances of `String` and converts it to a
    JSONSchema object that looks like `{'type': 'string'}`.

    :param str attr: The attribute to set
    """

    def wrapper(f):
        setattr(f, _method_marker, attr)
        return f

    return wrapper


def get_schema_fields(schema):
    """Retrieve all the names and field objects for a marshmallow Schema

    :param m.Schema schema:
    :returns: Yields tuples of the field name and the field itself
    :rtype: typing.Iterator[typing.Tuple[str, m.fields.Field]]
    """
    fields = []
    for name, field in schema.fields.items():
        prop = compat.get_data_key(field)
        fields.append((prop, field))
    return sorted(fields)


class MarshmallowConverter(object):
    """
    Abstract class for objects that convert Marshmallow objects to
    JSONSchema dictionaries.
    """

    MARSHMALLOW_TYPE = None

    def convert(self, obj, context):
        """
        Converts a Marshmallow object to a JSONSchema dictionary.

        This inspects the converter instance for methods that have been
        marked as attribute setters, calling them to set attributes on the
        resulting JSONSchema dictionary.

        :param m.Schema|m.fields.Field|Validator obj:
            The Marshmallow object to be converted
        :param _Context context:
            Various information to help the converter understand how to
            convert the object.
        :rtype: dict
        """
        jsonschema_obj = {}

        for _, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, _method_marker):
                val = method(obj, context)
                if val is not UNSET:
                    jsonschema_obj[getattr(method, _method_marker)] = val

        return jsonschema_obj


class SchemaConverter(MarshmallowConverter):
    """Converts Marshmallow Schema objects."""

    MARSHMALLOW_TYPE = m.Schema

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        if obj.many:
            return sw.array
        else:
            return sw.object_

    @sets_swagger_attr(sw.items)
    def get_items(self, obj, context):
        if not obj.many:
            return UNSET

        singular_obj = copy.deepcopy(obj)
        singular_obj.many = False

        return context.convert(singular_obj, context)

    @sets_swagger_attr(sw.properties)
    def get_properties(self, obj, context):
        if obj.many:
            return UNSET

        properties = {}

        for prop, field in get_schema_fields(obj):
            properties[prop] = context.convert(field, context)

        return properties

    @sets_swagger_attr(sw.required)
    def get_required(self, obj, context):
        if obj.many or obj.partial is True:
            return UNSET

        required = []
        obj_partial_is_collection = m.utils.is_collection(obj.partial)

        for name, field in obj.fields.items():
            if field.required:
                prop = compat.get_data_key(field)
                if obj_partial_is_collection and prop in obj.partial:
                    continue
                required.append(prop)

        if required and not obj.ordered:
            required = sorted(required)
        return required if required else UNSET

    @sets_swagger_attr(sw.description)
    def get_description(self, obj, context):
        if obj.many:
            return UNSET
        elif obj.__doc__:
            return obj.__doc__
        else:
            return UNSET

    @sets_swagger_attr(sw.title)
    def get_title(self, obj, context):
        if not obj.many:
            return get_swagger_title(obj)
        else:
            return UNSET


class FieldConverter(MarshmallowConverter):
    """
    Base Converter for Marshmallow Field objects.

    This should be extended for specific Field types.
    """

    MARSHMALLOW_TYPE = m.fields.Field

    def convert(self, obj, context):
        jsonschema_obj = super(FieldConverter, self).convert(obj, context)

        if obj.dump_only:
            jsonschema_obj["readOnly"] = True

        if obj.validate:
            validators = _normalize_validate(obj.validate)

            for validator in validators:
                try:
                    jsonschema_obj.update(
                        context.convert(
                            obj=validator,
                            context=_Context(
                                convert=context.convert,
                                memo=jsonschema_obj,
                                schema=context.schema,
                                openapi_version=context.openapi_version,
                            ),
                        )
                    )
                except UnregisteredType as e:
                    logging.debug(
                        "Unable to convert validator {validator}: {err}".format(
                            validator=validator, err=e
                        )
                    )

        if context.openapi_version == 3 and obj.allow_none:
            jsonschema_obj["nullable"] = True

        return jsonschema_obj

    @sets_swagger_attr(sw.default)
    def get_default(self, obj, context):
        if (
            obj.missing is not m.missing
            # Marshmallow accepts a callable for the default. This is tricky
            # to handle, so let's just ignore this for now.
            and not callable(obj.missing)
        ):
            return obj.missing
        else:
            return UNSET

    @sets_swagger_attr(sw.nullable)
    def get_nullable(self, obj, context):
        if context.openapi_version == 2 and obj.allow_none is not False:
            return True
        else:
            return UNSET

    @sets_swagger_attr(sw.description)
    def get_description(self, obj, context):
        if "description" in obj.metadata:
            return obj.metadata["description"]
        else:
            return UNSET


class ValidatorConverter(MarshmallowConverter):
    """
    Base Converter for Marshmallow Validator objects.

    This should be extended for specific Validator types.
    """

    MARSHMALLOW_TYPE = Validator


class DisallowExtraFieldsConverter(SchemaConverter):
    MARSHMALLOW_TYPE = DisallowExtraFieldsMixin

    @sets_swagger_attr(sw.additional_properties)
    def get_additional_properties(self, obj, context):
        return False


class NestedConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Nested

    def convert(self, obj, context):
        nested_obj = obj.nested

        # instantiate the object because the converter expects it to be
        inst = nested_obj()

        if obj.many:
            return {sw.type_: sw.array, sw.items: context.convert(inst, context)}
        else:
            return context.convert(inst, context)


class ListConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.List

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.array

    @sets_swagger_attr(sw.items)
    def get_items(self, obj, context):
        return context.convert(obj.container, context)


class DictConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Dict

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.object_


class IntegerConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Integer

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.integer


class StringConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.String

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.string


class NumberConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Number

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.number


class BooleanConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Boolean

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.boolean


class DateTimeConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.DateTime

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.string

    @sets_swagger_attr(sw.format_)
    def get_format(self, obj, context):
        return sw.date_time


class UUIDConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.UUID

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.string

    @sets_swagger_attr(sw.format_)
    def get_format(self, obj, context):
        return sw.uuid


class DateConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Date

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        return sw.string

    @sets_swagger_attr(sw.format_)
    def get_format(self, obj, context):
        return sw.date


class MethodConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Method

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        if "swagger_type" in obj.metadata:
            return obj.metadata["swagger_type"]
        else:
            raise ValueError(
                'Must include "swagger_type" ' "keyword argument in Method field"
            )


class FunctionConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Function

    @sets_swagger_attr(sw.type_)
    def get_type(self, obj, context):
        if "swagger_type" in obj.metadata:
            return obj.metadata["swagger_type"]
        else:
            raise ValueError(
                'Must include "swagger_type" ' "keyword argument in Function field"
            )


class ConstantConverter(FieldConverter):
    MARSHMALLOW_TYPE = m.fields.Constant

    @sets_swagger_attr(sw.enum)
    def get_enum(self, obj, context):
        return [obj.constant]


class CsvArrayConverter(ListConverter):
    MARSHMALLOW_TYPE = CommaSeparatedList

    @sets_swagger_attr(sw.collection_format)
    def get_collection_format(self, obj, context):
        return sw.csv if context.openapi_version == 2 else UNSET

    @sets_swagger_attr(sw.style)
    def get_style(self, obj, context):
        return sw.simple if context.openapi_version == 3 else UNSET


class MultiArrayConverter(ListConverter):
    MARSHMALLOW_TYPE = QueryParamList

    @sets_swagger_attr(sw.collection_format)
    def get_collection_format(self, obj, context):
        return sw.multi if context.openapi_version == 2 else UNSET

    @sets_swagger_attr(sw.explode)
    def get_explode(self, obj, context):
        return True if context.openapi_version == 3 else UNSET


class RangeConverter(ValidatorConverter):
    MARSHMALLOW_TYPE = Range

    @sets_swagger_attr(sw.minimum)
    def get_minimum(self, obj, context):
        if obj.min is not None:
            return obj.min
        else:
            return UNSET

    @sets_swagger_attr(sw.maximum)
    def get_maximum(self, obj, context):
        if obj.max is not None:
            return obj.max
        else:
            return UNSET


class OneOfConverter(ValidatorConverter):
    MARSHMALLOW_TYPE = OneOf

    @sets_swagger_attr(sw.enum)
    def get_enum(self, obj, context):
        return list(obj.choices)


class LengthConverter(ValidatorConverter):
    MARSHMALLOW_TYPE = Length

    @sets_swagger_attr(sw.min_items)
    def get_minimum_items(self, obj, context):
        if context.memo[sw.type_] == sw.array:
            if obj.min is not None:
                return obj.min
        return UNSET

    @sets_swagger_attr(sw.max_items)
    def get_maximum_items(self, obj, context):
        if context.memo[sw.type_] == sw.array:
            if obj.max is not None:
                return obj.max
        return UNSET

    @sets_swagger_attr(sw.min_length)
    def get_minimum_length(self, obj, context):
        if context.memo[sw.type_] == sw.string:
            if obj.min is not None:
                return obj.min
        return UNSET

    @sets_swagger_attr(sw.max_length)
    def get_maximum_length(self, obj, context):
        if context.memo[sw.type_] == sw.string:
            if obj.max is not None:
                return obj.max
        return UNSET


class ConverterRegistry(object):
    """
    Registry for MarshmallowConverters.

    Schemas for responses, query strings, request bodies, etc. need to
    be converted differently. For example, response schemas as "dump"ed and
    request body schemas are "loaded". For another example, query strings
    don't support nesting.

    This registry also allows for additional converters to be added for custom
    Marshmallow types.
    """

    def __init__(self):
        self._type_map = {}
        self._validator_map = {}

    def register_type(self, converter):
        """
        Registers a converter.

        :param MarshmallowConverter converter:
        """
        self._type_map[converter.MARSHMALLOW_TYPE] = converter

    def register_types(self, converters):
        """
        Registers multiple converters.

        :param iterable[MarshmallowConverter] converters:
        """
        for converter in converters:
            self.register_type(converter)

    def _get_converter_for_type(self, obj):
        """
        Locates the registered converter for a given type.
        :param obj: instance to convert
        :return: converter for type of instance
        """
        method_resolution_order = obj.__class__.__mro__

        for cls in method_resolution_order:
            if cls in self._type_map:
                return self._type_map[cls]
        else:
            raise UnregisteredType(
                "No registered type found in method resolution order: {mro}\n"
                "Registered types: {types}".format(
                    mro=method_resolution_order, types=list(self._type_map.keys())
                )
            )

    def _convert(self, obj, context):
        """
        Converts a Marshmallow object to a JSONSchema dictionary.

        :param m.Schema|m.fields.Field|Validator obj:
            The Marshmallow object to be converted
        :param _Context context:
            Various information to help the converter understand how to
            convert the given object.

            This helps with all the recursive nonsense.
        :rtype: dict
        """
        return self._get_converter_for_type(obj).convert(obj=obj, context=context)

    def convert(self, obj, openapi_version=2):
        """
        Converts a Marshmallow object to a JSONSchema dictionary.

        :param m.Schema|m.fields.Field|Validator obj:
            The Marshmallow object to be converted
        :param int openapi_version: major version of OpenAPI to convert obj for
        :rtype: dict
        """
        return self._convert(
            obj=obj,
            context=_Context(
                convert=self._convert,
                memo={},
                schema=obj,
                openapi_version=openapi_version,
            ),
        )


ALL_CONVERTERS = tuple(
    [
        klass()
        for _, klass in inspect.getmembers(sys.modules[__name__], inspect.isclass)
        if issubclass(klass, MarshmallowConverter)
    ]
)

query_string_converter_registry = ConverterRegistry()
query_string_converter_registry.register_types(
    [
        BooleanConverter(),
        CsvArrayConverter(),
        DateConverter(),
        DateTimeConverter(),
        FunctionConverter(),
        IntegerConverter(),
        LengthConverter(),
        ListConverter(),
        MethodConverter(),
        MultiArrayConverter(),
        NumberConverter(),
        OneOfConverter(),
        RangeConverter(),
        SchemaConverter(),
        StringConverter(),
        UUIDConverter(),
        ConstantConverter(),
    ]
)

headers_converter_registry = ConverterRegistry()
headers_converter_registry.register_types(
    [
        BooleanConverter(),
        CsvArrayConverter(),
        DateConverter(),
        DateTimeConverter(),
        FunctionConverter(),
        IntegerConverter(),
        LengthConverter(),
        ListConverter(),
        MethodConverter(),
        MultiArrayConverter(),
        NumberConverter(),
        OneOfConverter(),
        RangeConverter(),
        SchemaConverter(),
        StringConverter(),
        UUIDConverter(),
        ConstantConverter(),
    ]
)

request_body_converter_registry = ConverterRegistry()
request_body_converter_registry.register_types(
    [
        BooleanConverter(),
        DateConverter(),
        DateTimeConverter(),
        DictConverter(),
        DisallowExtraFieldsConverter(),
        FunctionConverter(),
        IntegerConverter(),
        LengthConverter(),
        ListConverter(),
        MethodConverter(),
        NestedConverter(),
        NumberConverter(),
        OneOfConverter(),
        RangeConverter(),
        SchemaConverter(),
        StringConverter(),
        UUIDConverter(),
        ConstantConverter(),
    ]
)

response_converter_registry = ConverterRegistry()
response_converter_registry.register_types(
    [
        BooleanConverter(),
        DateConverter(),
        DateTimeConverter(),
        DictConverter(),
        DisallowExtraFieldsConverter(),
        FunctionConverter(),
        IntegerConverter(),
        LengthConverter(),
        ListConverter(),
        MethodConverter(),
        NestedConverter(),
        NumberConverter(),
        OneOfConverter(),
        RangeConverter(),
        SchemaConverter(),
        StringConverter(),
        UUIDConverter(),
        ConstantConverter(),
    ]
)
