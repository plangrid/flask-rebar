"""
    Test Validation
    ~~~~~~~~~~~~~~~

    Tests for the Marshmallow extensions.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from datetime import datetime
from unittest import TestCase
from pytest import mark

from marshmallow import __version_info__ as MARSHMALLOW_VERSION
from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields
from marshmallow.validate import OneOf, Range
from werkzeug.datastructures import MultiDict

from flask_rebar import compat
from flask_rebar import rebar
from flask_rebar.utils.request_utils import normalize_schema
from flask_rebar.validation import RequireOnDumpMixin
from flask_rebar.validation import CommaSeparatedList
from flask_rebar.validation import QueryParamList
from tests.test_rebar import create_rebar_app


class NoRequireOnDumpMixinSchema(Schema):
    optional = fields.Str()
    value_optional = fields.Str(required=True, allow_none=True)
    value_required = fields.Str(required=True, allow_none=False)
    validation_required = fields.DateTime(required=True, allow_none=False)
    one_of_validation = fields.String(required=True, validate=OneOf(["a", "b"]))
    dump_only = fields.Integer(dump_only=True)  # type: ignore


class RequireOnDumpMixinSchema(NoRequireOnDumpMixinSchema, RequireOnDumpMixin):
    pass


class InnerNested(Schema, RequireOnDumpMixin):
    inner_dump_only = fields.String(dump_default="Inner dump-only", dump_only=True)
    inner_nested = fields.Nested(RequireOnDumpMixinSchema)
    inner_nested_dump_only = fields.Nested(RequireOnDumpMixinSchema, dump_only=True)
    inner_nested_list = fields.List(fields.Nested(RequireOnDumpMixinSchema))
    validated = fields.Integer(required=False, validate=Range(42, 99))


class OuterNested(Schema, RequireOnDumpMixin):
    outer_dump_only = fields.String(dump_default="Outer dump-only", dump_only=True)
    nested = fields.Nested(InnerNested)
    nested_list = fields.List(fields.Nested(InnerNested))


class OuterNestedNone(Schema, RequireOnDumpMixin):
    nested = fields.Nested(InnerNested, allow_none=True)


class RequireOutputMixinTest(TestCase):
    def setUp(self):
        super().setUp()
        self.validated_schema = normalize_schema(RequireOnDumpMixinSchema)
        self.unvalidated_schema = normalize_schema(NoRequireOnDumpMixinSchema)
        self.data = {
            "value_required": "abc",
            "value_optional": None,
            "validation_required": datetime.now(),
            "one_of_validation": "a",
        }

    def test_nominal(self):
        self.validated_schema.dump(self.data)

    def test_required_missing(self):
        del self.data["value_required"]
        with self.assertRaises(ValidationError) as ctx:
            compat.dump(self.validated_schema, self.data)
        self.assertIn("value_required", ctx.exception.messages)

    def test_required_none(self):
        self.data["value_required"] = None
        with self.assertRaises(ValidationError) as ctx:
            compat.dump(self.validated_schema, self.data)
        self.assertIn("value_required", ctx.exception.messages)

    def test_value_optional_missing(self):
        del self.data["value_optional"]
        with self.assertRaises(ValidationError) as ctx:
            compat.dump(self.validated_schema, self.data)
        self.assertIn("value_optional", ctx.exception.messages)

    def test_validation_works(self):
        self.data["validation_required"] = "123"
        with self.assertRaises(ValidationError) as ctx:
            compat.dump(self.validated_schema, self.data)
        # it's some sort of date error
        self.assertIn(
            "'str' object has no attribute 'isoformat'", ctx.exception.messages[0]
        )

    def test_required_failed_validate(self):
        self.data["one_of_validation"] = "c"
        with self.assertRaises(ValidationError) as ctx:
            compat.dump(self.validated_schema, self.data)
        self.assertIn("one_of_validation", ctx.exception.messages)

    def test_dump_only(self):
        self.data["dump_only"] = 42
        result = compat.dump(self.validated_schema, self.data)
        self.assertEqual(result["dump_only"], 42)

    def test_validation_opt_in(self):
        rebar_instance = rebar.Rebar()
        app = create_rebar_app(rebar_instance)

        self.data["one_of_validation"] = "c"
        with app.app_context():
            # explicit global opt-in:
            rebar_instance.validate_on_dump = True
            with self.assertRaises(ValidationError):
                compat.dump(self.unvalidated_schema, self.data)

            # explicit global opt-out:
            rebar_instance.validate_on_dump = False
            result = compat.dump(self.unvalidated_schema, self.data)
            self.assertEqual(result["one_of_validation"], "c")  # invalid but no error

            # with explicit opt-out, schema without mixin:
            result = compat.dump(self.unvalidated_schema, self.data)
            self.assertEqual(result["one_of_validation"], "c")  # invalid but no error

            # with explicit opt-out, but schema requiring val:
            with self.assertRaises(ValidationError):
                compat.dump(self.validated_schema, self.data)

    def test_top_level_list(self):
        data = [self.data.copy() for _ in range(3)]
        schema = RequireOnDumpMixinSchema(many=True)
        result = compat.dump(schema, data)
        self.assertEqual(len(result), len(data))
        data[1]["one_of_validation"] = "c"
        with self.assertRaises(ValidationError):
            compat.dump(schema, data)


class TestComplexNesting(TestCase):
    """
    Test cases for compat.dump with various cases in nested schemas.
    Note we use RequireOnDumpMixin in these Schemas so validation is always on.
    """

    def setUp(self):
        self.base_valid_inner_data = {
            "value_required": "abc",
            "value_optional": None,
            "validation_required": datetime.now(),
            "one_of_validation": "a",
        }

        self.base_valid_inner_wrapper = {
            "inner_nested": self.base_valid_inner_data.copy(),
            "inner_nested_list": [self.base_valid_inner_data.copy() for _ in range(3)],
        }

        self.base_valid_outer_wrapper = {
            "nested": self.base_valid_inner_wrapper.copy(),
            "nested_list": [self.base_valid_inner_wrapper.copy() for _ in range(3)],
        }

    @mark.skipif(
        MARSHMALLOW_VERSION < (3, 5),
        reason="https://github.com/marshmallow-code/marshmallow/issues/1497",
    )
    def test_dump_only_fields_defaults(self):
        """Our handling of dump_only fields respects defaults"""
        result = compat.dump(OuterNested(), self.base_valid_outer_wrapper)
        self.assertEqual(result["outer_dump_only"], "Outer dump-only")
        self.assertEqual(result["nested"]["inner_dump_only"], "Inner dump-only")
        self.assertNotIn(
            "dump_only", result["nested"]["inner_nested"]
        )  # no default for this one..
        for nested_item in result["nested_list"]:
            self.assertEqual(nested_item["inner_dump_only"], "Inner dump-only")
            for nested_nested_item in nested_item["inner_nested_list"]:
                self.assertNotIn(
                    "dump_only", nested_nested_item
                )  # no default for this one

    @mark.skipif(
        MARSHMALLOW_VERSION < (3, 5),
        reason="https://github.com/marshmallow-code/marshmallow/issues/1497",
    )
    def test_dump_only_fields_specified(self):
        """Our handling of dump_only fields preserves provided values"""
        self.base_valid_outer_wrapper["outer_dump_only"] = "Outer supplied"
        self.base_valid_outer_wrapper["nested"]["inner_dump_only"] = "Inner supplied"
        self.base_valid_outer_wrapper["nested"]["inner_nested"]["dump_only"] = 42
        self.base_valid_inner_wrapper["inner_nested_list"][1]["dump_only"] = 99
        self.base_valid_outer_wrapper["nested_list"][1][
            "inner_dump_only"
        ] = "Inner nested 1"
        result = compat.dump(OuterNested(), self.base_valid_outer_wrapper)
        self.assertEqual(result["outer_dump_only"], "Outer supplied")
        self.assertEqual(result["nested"]["inner_dump_only"], "Inner supplied")
        self.assertEqual(result["nested"]["inner_nested"]["dump_only"], 42)
        for i, nested_item in enumerate(result["nested_list"]):
            if i == 1:
                self.assertEqual(nested_item["inner_dump_only"], "Inner nested 1")
            else:
                self.assertEqual(nested_item["inner_dump_only"], "Inner dump-only")
            for j, nested_nested_item in enumerate(nested_item["inner_nested_list"]):
                if j == 1:
                    self.assertEqual(nested_nested_item["dump_only"], 99)
                else:
                    self.assertNotIn("dump_only", nested_nested_item)

    def test_validation_nested(self):
        """compat.dump validation works with nested schemas"""
        data = self.base_valid_outer_wrapper
        data["nested"]["validated"] = 999
        with self.assertRaises(ValidationError):
            compat.dump(OuterNested(), data)

    def test_validation_deep_nested(self):
        """compat.dump validation works with deeply nested schemas"""
        data = self.base_valid_outer_wrapper
        data["nested"]["inner_nested"]["one_of_validation"] = "z"
        with self.assertRaises(ValidationError):
            compat.dump(OuterNested(), data)

    def test_validation_nested_list(self):
        """compat.dump validation works with lists of nested schemas"""
        data = self.base_valid_outer_wrapper
        data["nested"]["inner_nested_list"][2]["one_of_validation"] = "z"
        with self.assertRaises(ValidationError):
            compat.dump(OuterNested(), data)

    def test_validation_nested_none(self):
        """compat.dump validation works with allow_none nested schemas"""
        data = self.base_valid_outer_wrapper
        data["nested"] = None
        result = compat.dump(OuterNestedNone(), data)
        self.assertEqual(result["nested"], None)


class StringList(Schema):
    foos = CommaSeparatedList(fields.String())


class IntegerList(Schema):
    foos = CommaSeparatedList(fields.Integer())


class TestCommaSeparatedList(TestCase):
    def test_deserialize(self):
        data = compat.load(StringList(), {"foos": "bar"})
        self.assertEqual(data["foos"], ["bar"])

        data = compat.load(StringList(), {"foos": "bar,baz"})
        self.assertEqual(data["foos"], ["bar", "baz"])

        data = compat.load(IntegerList(), {"foos": "1,2"})
        self.assertEqual(data["foos"], [1, 2])

    def test_serialize(self):
        data = compat.dump(StringList(), {"foos": ["bar"]})
        self.assertEqual(data["foos"], "bar")

        data = compat.dump(StringList(), {"foos": ["bar", "baz"]})
        self.assertEqual(data["foos"], "bar,baz")

        data = compat.dump(IntegerList(), {"foos": [1, 2]})
        self.assertEqual(data["foos"], "1,2")

    def test_deserialize_errors(self):
        with self.assertRaises(ValidationError) as ctx:
            compat.load(IntegerList(), {"foos": "1,two"})

        self.assertEqual(
            ctx.exception.messages, {"foos": {1: ["Not a valid integer."]}}
        )

    def test_serialize_errors(self):
        rebar_instance = rebar.Rebar()
        app = create_rebar_app(rebar_instance)
        with app.app_context():
            rebar_instance.validate_on_dump = (
                True  # cause ValueError to be wrapped in ValidationError
            )
            with self.assertRaises(ValidationError) as ctx:
                compat.dump(IntegerList(), {"foos": [42, "two"]})

            self.assertEqual(
                ctx.exception.messages,
                ["invalid literal for int() with base 10: 'two'"],
            )


class StringQuery(Schema):
    foos = QueryParamList(fields.String())


class IntegerQuery(Schema):
    foos = QueryParamList(fields.Integer())


class TestQueryParamList(TestCase):
    def test_deserialize(self):
        query = MultiDict([("foos", "bar")])
        data = compat.load(StringQuery(), query)
        self.assertEqual(data["foos"], ["bar"])

        query = MultiDict([("foos", "bar"), ("foos", "baz")])
        data = compat.load(StringQuery(), query)
        self.assertEqual(data["foos"], ["bar", "baz"])

        query = MultiDict([("foos", 1), ("foos", 2)])
        data = compat.load(IntegerQuery(), query)
        self.assertEqual(data["foos"], [1, 2])

    def test_deserialize_errors(self):
        query = MultiDict([("foos", 1), ("foos", "two")])

        with self.assertRaises(ValidationError) as ctx:
            compat.load(IntegerQuery(), query)

        self.assertEqual(
            ctx.exception.messages, {"foos": {1: ["Not a valid integer."]}}
        )


class DataKeySchema(RequireOnDumpMixin, Schema):
    test_field = fields.String(data_key="testField")


class TestDataKey(TestCase):
    def test_dump_and_validate_with_data_key(self):
        result = compat.dump(DataKeySchema(), {"test_field": "abc"})
        self.assertEqual(result, {"testField": "abc"})
