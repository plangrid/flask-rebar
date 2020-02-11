"""
    Test Request Utilities
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests for the request utilities.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import unittest
from tests.helpers import make_test_response

from flask import Flask
from marshmallow import fields, ValidationError

from flask_rebar import validation, response, marshal


class TestResponseFormatting(unittest.TestCase):
    def setUp(self):
        self.app = self.create_app()
        self.app.response_class = make_test_response(self.app.response_class)

    def create_app(self):
        app = Flask(__name__)

        return app

    def test_single_resource_response(self):
        @self.app.route("/single_resource")
        def handler():
            return response(data={"foo": "bar"})

        resp = self.app.test_client().get("/single_resource")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"foo": "bar"})
        self.assertEqual(resp.content_type, "application/json")

    def test_single_resource_response_with_status_code(self):
        @self.app.route("/single_resource")
        def handler():
            return response(data={"foo": "bar"}, status_code=201)

        resp = self.app.test_client().get("/single_resource")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json, {"foo": "bar"})
        self.assertEqual(resp.content_type, "application/json")

    def test_single_resource_response_with_headers(self):
        header_key = "X-Foo"
        header_value = "bar"

        @self.app.route("/single_resource")
        def handler():
            return response(data={"foo": "bar"}, headers={header_key: header_value})

        resp = self.app.test_client().get("/single_resource")
        self.assertEqual(resp.headers[header_key], header_value)
        self.assertEqual(resp.json, {"foo": "bar"})
        self.assertEqual(resp.content_type, "application/json")


class SchemaForMarshaling(validation.ResponseSchema):
    foo = fields.Integer()


class TestMarshal(unittest.TestCase):
    def test_marshal(self):
        marshaled = marshal(data={"foo": 1}, schema=SchemaForMarshaling)
        self.assertEqual(marshaled, {"foo": 1})

        # Also works with an instance of the schema
        marshaled = marshal(data={"foo": 1}, schema=SchemaForMarshaling())

        self.assertEqual(marshaled, {"foo": 1})

    def test_marshal_errors(self):
        with self.assertRaises(ValidationError):
            marshal(data={"foo": "bar"}, schema=SchemaForMarshaling)
