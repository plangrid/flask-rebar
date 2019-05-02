"""
    Test Generator Utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Unit tests for the generator utilities.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import unittest

from flask_rebar.swagger_generation.generator_utils import PathArgument
from flask_rebar.swagger_generation.generator_utils import flatten
from flask_rebar.swagger_generation.generator_utils import format_path_for_swagger


class TestFlatten(unittest.TestCase):
    def setUp(self):
        super(TestFlatten, self).setUp()
        self.maxDiff = None

    def test_flatten(self):
        input_ = {
            "type": "object",
            "title": "x",
            "properties": {
                "a": {
                    "type": "object",
                    "title": "y",
                    "properties": {"b": {"type": "integer"}},
                },
                "b": {"type": "string"},
            },
        }

        expected_schema = {"$ref": "#/definitions/x"}

        expected_definitions = {
            "x": {
                "type": "object",
                "title": "x",
                "properties": {
                    "a": {"$ref": "#/definitions/y"},
                    "b": {"type": "string"},
                },
            },
            "y": {
                "type": "object",
                "title": "y",
                "properties": {"b": {"type": "integer"}},
            },
        }

        schema, definitions = flatten(input_, base="#/definitions")
        self.assertEqual(schema, expected_schema)
        self.assertEqual(definitions, expected_definitions)

    def test_flatten_array(self):
        input_ = {
            "type": "array",
            "title": "x",
            "items": {
                "type": "array",
                "title": "y",
                "items": {
                    "type": "object",
                    "title": "z",
                    "properties": {"a": {"type": "integer"}},
                },
            },
        }

        expected_schema = {
            "type": "array",
            "title": "x",
            "items": {
                "type": "array",
                "title": "y",
                "items": {"$ref": "#/definitions/z"},
            },
        }

        expected_definitions = {
            "z": {
                "type": "object",
                "title": "z",
                "properties": {"a": {"type": "integer"}},
            }
        }

        schema, definitions = flatten(input_, base="#/definitions")
        self.assertEqual(schema, expected_schema)
        self.assertEqual(definitions, expected_definitions)

    def test_flatten_subschemas(self):
        input_ = {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "title": "a",
                    "properties": {"a": {"type": "string"}},
                },
                {
                    "type": "array",
                    "title": "b",
                    "items": {
                        "type": "object",
                        "title": "c",
                        "properties": {"a": {"type": "string"}},
                    },
                },
                {
                    "anyOf": [
                        {
                            "type": "object",
                            "title": "d",
                            "properties": {"a": {"type": "string"}},
                        }
                    ]
                },
            ]
        }

        expected_schema = {
            "anyOf": [
                {"type": "null"},
                {"$ref": "#/definitions/a"},
                {"type": "array", "title": "b", "items": {"$ref": "#/definitions/c"}},
                {"anyOf": [{"$ref": "#/definitions/d"}]},
            ]
        }

        expected_definitions = {
            "a": {
                "type": "object",
                "title": "a",
                "properties": {"a": {"type": "string"}},
            },
            "c": {
                "type": "object",
                "title": "c",
                "properties": {"a": {"type": "string"}},
            },
            "d": {
                "type": "object",
                "title": "d",
                "properties": {"a": {"type": "string"}},
            },
        }

        schema, definitions = flatten(input_, base="#/definitions")
        self.assertEqual(schema, expected_schema)
        self.assertEqual(definitions, expected_definitions)


class TestFormatPathForSwagger(unittest.TestCase):
    def test_format_path(self):
        res, args = format_path_for_swagger(
            "/projects/<uuid:project_uid>/foos/<foo_uid>"
        )

        self.assertEqual(res, "/projects/{project_uid}/foos/{foo_uid}")

        self.assertEqual(
            args,
            (
                PathArgument(name="project_uid", type="uuid"),
                PathArgument(name="foo_uid", type="string"),
            ),
        )

    def test_no_args(self):
        res, args = format_path_for_swagger("/health")

        self.assertEqual(res, "/health")
        self.assertEqual(args, tuple())
