"""
    Test Marshmallow to Swagger
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests for the Marshmallow to Swagger converters.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import unittest

import marshmallow as m
from marshmallow import validate as v

from flask_rebar.swagger_generation.marshmallow_to_swagger import ALL_CONVERTERS
from flask_rebar.swagger_generation.marshmallow_to_swagger import ConverterRegistry
from flask_rebar.validation import CommaSeparatedList
from flask_rebar.validation import QueryParamList
from flask_rebar.validation import DisallowExtraFieldsMixin
from tests.helpers import skip_if_marshmallow_not_v2, skip_if_marshmallow_not_v3


class TestConverterRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ConverterRegistry()
        self.registry.register_types(ALL_CONVERTERS)

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

            schema = Foo()
            json_schema = self.registry.convert(schema)

            self.assertEqual(
                json_schema,
                {"type": "object", "title": "Foo", "properties": {"a": result}},
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
                {"type": "object", "title": "Foo", "properties": {"a": result}},
            )

    @skip_if_marshmallow_not_v2
    def test_dump_to(self):
        class Foo(m.Schema):
            a = m.fields.Integer(dump_to="b", required=True)

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Foo",
                "properties": {"b": {"type": "integer"}},
                "required": ["b"],
            },
        )

    @skip_if_marshmallow_not_v2
    def test_load_from(self):
        registry = ConverterRegistry()
        registry.register_types(ALL_CONVERTERS)

        class Foo(m.Schema):
            a = m.fields.Integer(load_from="b", required=True)

        schema = Foo()
        json_schema = registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Foo",
                "properties": {"b": {"type": "integer"}},
                "required": ["b"],
            },
        )

    @skip_if_marshmallow_not_v3
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
            },
        )

    def test_example(self):
        class Foo(m.Schema):
            b = m.fields.Integer(example="123", description="desc")

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Foo",
                "properties": {
                    "b": {"type": "integer", "example": "123", "description": "desc"}
                },
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
                "type": "object",
                "title": "Foo",
                "properties": {
                    "a": {
                        "type": "object",
                        "title": "Bar",
                        "properties": {"a": {"type": "integer"}},
                    }
                },
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
                "type": "array",
                "items": {
                    "type": "object",
                    "title": "Foo",
                    "properties": {"a": {"type": "integer"}},
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
                "type": "object",
                "title": "Foo",
                "properties": {
                    "a": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "title": "Bar",
                            "properties": {"a": {"type": "integer"}},
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
            {"type": "object", "title": "Foo", "properties": {"a": {"type": "string"}}},
        )

    def test_additional_properties(self):
        class Foo(DisallowExtraFieldsMixin, m.Schema):
            a = m.fields.Integer()

        schema = Foo()
        json_schema = self.registry.convert(schema)

        self.assertEqual(
            json_schema,
            {
                "type": "object",
                "title": "Foo",
                "properties": {"a": {"type": "integer"}},
                "additionalProperties": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
