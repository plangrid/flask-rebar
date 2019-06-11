"""
    Test Errors
    ~~~~~~~~~~~

    Tests for the exception to HTTP error transformation.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals

import json

from flask import Flask
from flask_testing import TestCase
from marshmallow import fields
from werkzeug.exceptions import BadRequest

from flask_rebar import messages, validation, response, Rebar
from flask_rebar.compat import MARSHMALLOW_V2
from flask_rebar import errors
from flask_rebar.utils.request_utils import get_json_body_params_or_400
from flask_rebar.utils.request_utils import get_query_string_params_or_400


class TestErrors(TestCase):
    ERROR_MSG = "Bamboozled!"

    def create_app(self):
        app = Flask(__name__)

        @app.route("/errors", methods=["GET"])
        def a_terrible_handler():
            raise errors.Conflict(msg=TestErrors.ERROR_MSG)

        @app.route("/uncaught_errors", methods=["GET"])
        def an_even_worse_handler():
            raise ArithmeticError()

        @app.route("/verbose_errors", methods=["GET"])
        def a_fancy_handler():
            raise errors.Conflict(
                msg=TestErrors.ERROR_MSG, additional_data={"foo": "bar"}
            )

        @app.route("/route_that_fails_validation", methods=["GET"])
        def validation_fails_handler():
            raise BadRequest()

        Rebar().init_app(app=app)

        return app

    def test_custom_http_errors_are_handled(self):
        resp = self.app.test_client().get("/errors")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content_type, "application/json")
        self.assertEqual(resp.json, {"message": TestErrors.ERROR_MSG})

    def test_custom_http_errors_can_have_additional_data(self):
        resp = self.app.test_client().get("/verbose_errors")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content_type, "application/json")
        self.assertEqual(resp.json, {"message": TestErrors.ERROR_MSG, "foo": "bar"})

    def test_default_400_errors_are_formatted_correctly(self):
        resp = self.app.test_client().get("/route_that_fails_validation")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.content_type, "application/json")
        self.assertTrue(
            resp.json.get("message")
        )  # don't care about exact message wording, just existence

    def test_default_404_errors_are_formatted_correctly(self):
        resp = self.app.test_client().get("/nonexistent")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content_type, "application/json")
        self.assertTrue(
            resp.json.get("message")
        )  # don't care about exact message wording, just existence

    def test_default_405_errors_are_formatted_correctly(self):
        resp = self.app.test_client().put("/errors")
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.content_type, "application/json")
        self.assertTrue(
            resp.json.get("message")
        )  # don't care about exact message wording, just existence

    def test_default_500_errors_are_formatted_correctly(self):
        resp = self.app.test_client().get("/uncaught_errors")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content_type, "application/json")
        self.assertEqual(resp.json, {"message": messages.internal_server_error})


class TestJsonBodyValidation(TestCase):
    def post_json(self, path, data):
        return self.app.test_client().post(
            path=path,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

    def create_app(self):
        app = Flask(__name__)
        Rebar().init_app(app=app)

        class NestedSchema(validation.RequestSchema):
            baz = fields.List(fields.Integer())

        class Schema(validation.RequestSchema):
            foo = fields.Integer(required=True)
            bar = fields.Email()
            nested = fields.Nested(NestedSchema)

        @app.route("/stuffs", methods=["POST"])
        def json_body_handler():
            data = get_json_body_params_or_400(schema=Schema)
            return response(data)

        return app

    def test_json_encoding_validation(self):
        resp = self.app.test_client().post(
            path="/stuffs", headers={"Content-Type": "application/json"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {"message": messages.empty_json_body})

        resp = self.app.test_client().post(
            path="/stuffs",
            data=json.dumps({"foo": 1}),
            headers={"Content-Type": "text/csv"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {"message": messages.unsupported_content_type})

        resp = self.app.test_client().post(
            path="/stuffs",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {"message": messages.invalid_json})

    def test_json_body_parameter_validation(self):
        # Only field errors
        resp = self.post_json(
            path="/stuffs", data={"foo": "one", "bar": "not-an-email"}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json,
            {
                "message": messages.body_validation_failed,
                "errors": {
                    "foo": "Not a valid integer.",
                    "bar": "Not a valid email address.",
                },
            },
        )

        # Only general errors
        resp = self.post_json(
            path="/stuffs", data={"foo": 1, "baz": "This is an unexpected field!"}
        )
        self.assertEqual(resp.status_code, 400)
        if MARSHMALLOW_V2:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.body_validation_failed,
                    "errors": {"_general": "Unexpected field: baz"},
                },
            )
        else:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.body_validation_failed,
                    "errors": {"baz": "Unknown field."},
                },
            )

        # Both field errors and general errors
        resp = self.post_json(
            path="/stuffs", data={"baz": "This is an unexpected field!"}
        )
        self.assertEqual(resp.status_code, 400)

        if MARSHMALLOW_V2:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.body_validation_failed,
                    "errors": {
                        "_general": "Unexpected field: baz",
                        "foo": "Missing data for required field.",
                    },
                },
            )
        else:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.body_validation_failed,
                    "errors": {
                        "baz": "Unknown field.",
                        "foo": "Missing data for required field.",
                    },
                },
            )

        # Happy path
        resp = self.post_json(path="/stuffs", data={"foo": 1})
        self.assertEqual(resp.status_code, 200)

    def test_representing_complex_errors(self):
        resp = self.post_json(
            path="/stuffs",
            data={
                "bam": "wow!",
                "nested": {"baz": ["one", "two"], "unexpected": "surprise!"},
            },
        )
        self.assertEqual(resp.status_code, 400)

        if MARSHMALLOW_V2:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.body_validation_failed,
                    "errors": {
                        "_general": "Unexpected field: bam",
                        "foo": "Missing data for required field.",
                        "nested": {
                            "_general": "Unexpected field: unexpected",
                            "baz": {
                                "0": "Not a valid integer.",
                                "1": "Not a valid integer.",
                            },
                        },
                    },
                },
            )
        else:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.body_validation_failed,
                    "errors": {
                        "bam": "Unknown field.",
                        "foo": "Missing data for required field.",
                        "nested": {
                            "unexpected": "Unknown field.",
                            "baz": {
                                "0": "Not a valid integer.",
                                "1": "Not a valid integer.",
                            },
                        },
                    },
                },
            )

    def test_invalid_json_error(self):
        resp = self.app.test_client().post(
            path="/stuffs",
            data='"Im technically valid JSON, but not an object"',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {"message": messages.invalid_json})


class TestQueryStringValidation(TestCase):
    def create_app(self):
        app = Flask(__name__)
        Rebar().init_app(app=app)

        class Schema(validation.RequestSchema):
            foo = fields.Integer(required=True)
            bar = fields.Boolean()
            baz = validation.CommaSeparatedList(fields.Integer())

        @app.route("/stuffs", methods=["GET"])
        def query_string_handler():
            params = get_query_string_params_or_400(schema=Schema())
            return response(data=params)

        return app

    def test_query_string_parameter_validation(self):
        resp = self.app.test_client().get(path="/stuffs?foo=one")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json,
            {
                "message": messages.query_string_validation_failed,
                "errors": {"foo": "Not a valid integer."},
            },
        )

        resp = self.app.test_client().get(path="/stuffs?bar=true")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json,
            {
                "message": messages.query_string_validation_failed,
                "errors": {"foo": "Missing data for required field."},
            },
        )

        resp = self.app.test_client().get(path="/stuffs?foo=1&unexpected=true")
        self.assertEqual(resp.status_code, 400)
        if MARSHMALLOW_V2:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.query_string_validation_failed,
                    "errors": {"_general": "Unexpected field: unexpected"},
                },
            )
        else:
            self.assertEqual(
                resp.json,
                {
                    "message": messages.query_string_validation_failed,
                    "errors": {"unexpected": "Unknown field."},
                },
            )

        resp = self.app.test_client().get(path="/stuffs?foo=1&bar=true&baz=1,2,3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"foo": 1, "bar": True, "baz": [1, 2, 3]})
