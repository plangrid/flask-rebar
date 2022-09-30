"""
    Test Generator Utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Unit tests for the generator utilities.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import unittest
from unittest.mock import MagicMock

from flask_rebar.swagger_generation.generator_utils import PathArgument
from flask_rebar.swagger_generation.generator_utils import flatten
from flask_rebar.swagger_generation.generator_utils import format_path_for_swagger
from flask_rebar.swagger_generation.generator_utils import (
    add_docstring_to_path_definition,
)


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

        expected_schema = {"$ref": "#/definitions/x"}

        expected_definitions = {
            "x": {"type": "array", "title": "x", "items": {"$ref": "#/definitions/y"}},
            "y": {"type": "array", "title": "y", "items": {"$ref": "#/definitions/z"}},
            "z": {
                "type": "object",
                "title": "z",
                "properties": {"a": {"type": "integer"}},
            },
        }

        schema, definitions = flatten(input_, base="#/definitions")
        self.assertEqual(schema, expected_schema)
        self.assertEqual(definitions, expected_definitions)

    def test_flatten_anyof_with_title(self):
        input_ = {
            "anyOf": [
                {
                    "type": "object",
                    "title": "a",
                    "properties": {"a": {"type": "string"}},
                },
                {
                    "type": "object",
                    "title": "b",
                    "properties": {"b": {"type": "string"}},
                },
            ],
            "title": "union",
        }

        expected_schema = {"$ref": "#/definitions/union"}

        expected_definitions = {
            "a": {
                "type": "object",
                "title": "a",
                "properties": {"a": {"type": "string"}},
            },
            "b": {
                "type": "object",
                "title": "b",
                "properties": {"b": {"type": "string"}},
            },
            "union": {
                "anyOf": [{"$ref": "#/definitions/a"}, {"$ref": "#/definitions/b"}],
                "title": "union",
            },
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
                {"$ref": "#/definitions/b"},
                {"anyOf": [{"$ref": "#/definitions/d"}]},
            ]
        }

        expected_definitions = {
            "a": {
                "type": "object",
                "title": "a",
                "properties": {"a": {"type": "string"}},
            },
            "b": {"type": "array", "title": "b", "items": {"$ref": "#/definitions/c"}},
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


class TestAddDocStringToPathDefinition(unittest.TestCase):
    @staticmethod
    def _generate_mock_method_with_docstring(docstring):
        mock_method = MagicMock()
        mock_method.func.__doc__ = docstring
        return mock_method

    def test_when_parse_docstring_is_no_empty_docstring(self):
        mock_method = self._generate_mock_method_with_docstring("")
        path_definition = {"get": {}}
        add_docstring_to_path_definition(path_definition, "get", mock_method, False)
        expected = {"get": {}}
        self.assertEqual(expected["get"], path_definition["get"])

    def test_when_parse_docstring_is_no_short_docstring(self):
        mock_method = self._generate_mock_method_with_docstring("test")
        path_definition = {"get": {}}
        add_docstring_to_path_definition(path_definition, "get", mock_method, False)
        expected = {"get": {"description": "test"}}
        self.assertEqual(expected["get"], path_definition["get"])

    def test_when_parse_docstring_is_no_long_docstring(self):
        docstring = "\ntest summary\n\n    test description\n"
        mock_method = self._generate_mock_method_with_docstring(docstring)
        path_definition = {"get": {}}
        add_docstring_to_path_definition(path_definition, "get", mock_method, False)
        expected = {"get": {"description": docstring}}
        self.assertEqual(expected["get"], path_definition["get"])

    def test_when_parse_docstring_is_yes_empty_docstring(self):
        mock_method = self._generate_mock_method_with_docstring("")
        path_definition = {"get": {}}
        add_docstring_to_path_definition(path_definition, "get", mock_method, True)
        expected = {"get": {}}
        self.assertEqual(expected["get"], path_definition["get"])

    def test_when_parse_docstring_is_yes_short_docstring(self):
        mock_method = self._generate_mock_method_with_docstring("test")
        path_definition = {"get": {}}
        add_docstring_to_path_definition(path_definition, "get", mock_method, True)
        expected = {"get": {"summary": "test"}}
        self.assertEqual(expected["get"], path_definition["get"])

    def test_when_parse_docstring_is_yes_long_docstring(self):
        docstring = "\ntest summary\n\n    test description\n"
        mock_method = self._generate_mock_method_with_docstring(docstring)
        path_definition = {"get": {}}
        add_docstring_to_path_definition(path_definition, "get", mock_method, True)
        expected = {
            "get": {"description": "test description", "summary": "test summary"}
        }
        self.assertEqual(expected["get"], path_definition["get"])
