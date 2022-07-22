"""
    Test Marshmallow to Swagger
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the Marshmallow to Swagger converters.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import enum
import unittest
from unittest import TestCase

import marshmallow as m
import marshmallow_enum as me
from marshmallow import validate as v
from parametrize import parametrize

from flask_rebar.swagger_generation.marshmallow_to_swagger import ALL_CONVERTERS
from flask_rebar.swagger_generation.marshmallow_to_swagger import ConverterRegistry
from flask_rebar.validation import CommaSeparatedList
from flask_rebar.validation import QueryParamList


class StopLight(enum.Enum):
    green = 1
    yellow = 2
    red = 3


class TestConverterRegistry(TestCase):
    def setUp(self):
        self.registry = ConverterRegistry()
        self.registry.register_types(ALL_CONVERTERS)

    def do_nothing(self):
        pass

    def test_primitive_types(self):
        for field, result in [
            (m.fields.Integer(), {"type": "integer"}),
            (m.fields.String(), {"type": "string"}),
            (m.fields.Number(), {"type": "number"}),
            (m.fields.DateTime(), {"type": "string", "format": "date-time"}),
            (m.fields.Date(), {"type": "string", "format": "date"}),
            (m.fields.UUID(), {"type": "string", "format": "uuid"}),
            (m.fields.Boolean(), {"type": "boolean"}),
            (m.fields.URL(), {"type": "string"}),
            (m.fields.Email(), {"type": "string"}),
            (m.fields.Constant("foo"), {"enum": ["foo"], "default": "foo"}),
            (m.fields.Integer(missing=5), {"type": "integer", "default": 5}),
            (m.fields.Integer(dump_only=True), {"type": "integer", "readOnly": True}),
            (m.fields.Integer(missing=lambda: 5), {"type": "integer"}),
            (
                me.EnumField(StopLight),
                {"enum": ["green", "yellow", "red"], "type": "string"},
            ),
            (
                me.EnumField(StopLight, by_value=True),
                {"enum": [1, 2, 3], "type": "integer"},
            ),
            (
                m.fields.Integer(allow_none=True),
                {"type": "integer", "x-nullable": True},
            ),
            (
                m.fields.List(m.fields.Integer()),
                {"type": "array", "items": {"type": "integer"}},
            ),
            (
                m.fields.List(m.fields.Integer),
                {"type": "array", "items": {"type": "integer"}},
            ),
            (
                m.fields.Integer(description="blam!"),
                {"type": "integer", "description": "blam!"},
            ),
            (
                QueryParamList(m.fields.Integer()),
                {
                    "type": "array",
                    "items": {"type": "integer"},
                    "collectionFormat": "multi",
                },
            ),
            (
                CommaSeparatedList(m.fields.Integer()),
                {
                    "type": "array",
                    "items": {"type": "integer"},
                    "collectionFormat": "csv",
                },
            ),
            (
                m.fields.Integer(validate=v.Range(min=1)),
                {"type": "integer", "minimum": 1},
            ),
            (
                m.fields.Integer(validate=v.Range(max=9)),
                {"type": "integer", "maximum": 9},
            ),
            (
                m.fields.List(m.fields.Integer(), validate=v.Length(min=1)),
                {"type": "array", "items": {"type": "integer"}, "minItems": 1},
            ),
            (
                m.fields.List(m.fields.Integer(), validate=v.Length(max=9)),
                {"type": "array", "items": {"type": "integer"}, "maxItems": 9},
            ),
            (
                m.fields.String(validate=v.Length(min=1)),
                {"type": "string", "minLength": 1},
            ),
            (
                m.fields.String(validate=v.Length(max=9)),
                {"type": "string", "maxLength": 9},
            ),
            (
                m.fields.String(validate=v.OneOf(["a", "b"])),
                {"type": "string", "enum": ["a", "b"]},
            ),
            (m.fields.Dict(), {"type": "object"}),
            (
                m.fields.Method(serialize="x", deserialize="y", swagger_type="integer"),
                {"type": "integer"},
            ),
            (
                m.fields.Function(
                    serialize=lambda _: _,
                    deserialize=lambda _: _,
                    swagger_type="string",
                ),
                {"type": "string"},
            ),
            (m.fields.Integer(validate=lambda value: True), {"type": "integer"}),
        ]:

            class Foo(m.Schema):
                a = field

                # in marshmallow >= 3.11.x, if the 'serialize' / 'deserialize' functions for
                # a field.Method aren't defined, an exception will be raised.
                x = self.do_nothing
                y = self.do_nothing

            schema = Foo()
            json_schema = self.registry.convert(schema)

            self.assertEqual(
                json_schema,
                {
                    "additionalProperties": False,
                    "type": "object",
                    "title": "Foo",
                    "properties": {"a": result},
                },
            )

    def test_primitive_types_openapi_v3(self):
        for field, result in [
            (m.fields.Integer(allow_none=True), {"type": "integer", "nullable": True}),
            (
                QueryParamList(m.fields.Integer()),
                {"type": "array", "items": {"type": "integer"}, "explode": True},
            ),
            (
                CommaSeparatedList(m.fields.Integer()),
                {"type": "array", "items": {"type": "integer"}, "style": "simple"},
            ),
        ]:

            class Foo(m.Schema):
                a = field

            schema = Foo()
            json_schema = self.registry.convert(schema, openapi_version=3)

            self.assertEqual(
                json_schema,
                {
                    "additionalProperties": False,
                    "type": "object",
                    "title": "Foo",
                    "properties": {"a": result},
                },
            )

    def test_data_key(self):
        registry = ConverterRegistry()
        registry.register_types(ALL_CONVERTERS)

        class Foo(m.Schema):
            a = m.fields.Integer(data_key="b", required=True)

        schema = Foo()
        json_schema = registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Foo",
                "properties": {"b": {"type": "integer"}},
                "required": ["b"],
                "additionalProperties": False,
            },
        )

    def test_required(self):
        class Foo(m.Schema):
            b = m.fields.Integer(required=True)
            a = m.fields.Integer(required=True)
            c = m.fields.Integer()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {
                    "b": {"type": "integer"},
                    "a": {"type": "integer"},
                    "c": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        )

    def test_ordered_required(self):
        class Foo(m.Schema):
            b = m.fields.Integer(required=True)
            a = m.fields.Integer(required=True)
            c = m.fields.Integer()

            class Meta:
                ordered = True

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {
                    "b": {"type": "integer"},
                    "a": {"type": "integer"},
                    "c": {"type": "integer"},
                },
                "required": ["b", "a"],
            },
        )

    def test_partial(self):
        class Foo(m.Schema):
            b = m.fields.Integer(required=True)
            a = m.fields.Integer(required=True)
            c = m.fields.Integer()

        schema = Foo(partial=["b"])
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {
                    "b": {"type": "integer"},
                    "a": {"type": "integer"},
                    "c": {"type": "integer"},
                },
                "required": ["a"],
            },
        )

    def test_partial_all(self):
        class Foo(m.Schema):
            b = m.fields.Integer(required=True)
            a = m.fields.Integer(required=True)
            c = m.fields.Integer()

        schema = Foo(partial=True)
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {
                    "b": {"type": "integer"},
                    "a": {"type": "integer"},
                    "c": {"type": "integer"},
                },
            },
        )

    def test_object_description(self):
        class Foo(m.Schema):
            """I'm the description!"""

            a = m.fields.Integer()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "description": "I'm the description!",
                "properties": {"a": {"type": "integer"}},
            },
        )

    def test_nested(self):
        class Bar(m.Schema):
            a = m.fields.Integer()

        class Foo(m.Schema):
            a = m.fields.Nested(Bar)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {
                    "a": {
                        "type": "object",
                        "title": "Bar",
                        "properties": {"a": {"type": "integer"}},
                        "additionalProperties": False,
                    }
                },
            },
        )

    def test_self_referential_nested(self):
        # Issue 90
        # note for Marshmallow >= 3.3, preferred format is e.g.,:
        # m.fields.Nested(lambda: Foo(only=("d", "b")))
        # and passing "self" as a string is deprecated
        # but that doesn't work in < 3.3, so until 4.x we'll keep supporting/testing with "self"
        class Foo(m.Schema):
            a = m.fields.Nested("self", exclude=("a",))
            b = m.fields.Integer()
            c = m.fields.Nested("self", only=("d", "b"))
            d = m.fields.Email()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "properties": {
                    "a": {
                        "additionalProperties": False,
                        "properties": {
                            "b": {"type": "integer"},
                            "c": {
                                "additionalProperties": False,
                                "properties": {
                                    "b": {"type": "integer"},
                                    "d": {"type": "string"},
                                },
                                "title": "Foo",
                                "type": "object",
                            },
                            "d": {"type": "string"},
                        },
                        "title": "Foo",
                        "type": "object",
                    },
                    "b": {"type": "integer"},
                    "c": {
                        "additionalProperties": False,
                        "properties": {
                            "b": {"type": "integer"},
                            "d": {"type": "string"},
                        },
                        "title": "Foo",
                        "type": "object",
                    },
                    "d": {"type": "string"},
                },
                "title": "Foo",
                "type": "object",
                "additionalProperties": False,
            },
        )

    def test_many(self):
        class Foo(m.Schema):
            a = m.fields.Integer()

        schema = Foo(many=True)
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "array",
                "items": {
                    "type": "object",
                    "title": "Foo",
                    "properties": {"a": {"type": "integer"}},
                    "additionalProperties": False,
                },
            },
        )

    def test_nested_many(self):
        class Bar(m.Schema):
            a = m.fields.Integer()

        class Foo(m.Schema):
            a = m.fields.Nested(Bar, many=True)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {
                    "a": {
                        "additionalProperties": False,
                        "type": "array",
                        "items": {
                            "type": "object",
                            "title": "Bar",
                            "properties": {"a": {"type": "integer"}},
                            "additionalProperties": False,
                        },
                    }
                },
            },
        )

    def test_inheritance(self):
        class Foo(m.Schema):
            a = m.fields.Integer()

        class Bar(Foo):
            b = m.fields.Integer()

        schema = Bar()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Bar",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "additionalProperties": False,
            },
        )

    def test_converters_are_checked_up_the_mro_chain(self):
        class CustomString(m.fields.String):
            pass

        class Foo(m.Schema):
            a = CustomString()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Foo",
                "properties": {"a": {"type": "string"}},
                "additionalProperties": False,
            },
        )

    class FooDefault(m.Schema):  # default in marshmallow 3 will raise
        a = m.fields.Integer()

    class FooExplicitRaise(FooDefault):
        class Meta:
            unknown = m.RAISE

    class FooExplicitExclude(FooDefault):
        class Meta:
            unknown = m.EXCLUDE

    class FooExplicitInclude(FooDefault):
        class Meta:
            unknown = m.INCLUDE

    @parametrize(
        "schema_cls, expected_additional_value",
        [
            (FooDefault, False),
            (FooExplicitRaise, False),
            (FooExplicitExclude, False),
            (FooExplicitInclude, True),
        ],
    )
    def test_additional_properties(self, schema_cls, expected_additional_value):
        expected = {
            "type": "object",
            "title": schema_cls.__name__,
            "properties": {"a": {"type": "integer"}},
            "additionalProperties": expected_additional_value,
        }

        schema = schema_cls()
        json_schema = self.registry.convert(schema)
        self.assertEqual(json_schema, expected)


if __name__ == "__main__":
    unittest.main()
