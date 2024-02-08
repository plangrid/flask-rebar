"""
    Test Errors
    ~~~~~~~~~~~

    Tests for the exception to HTTP error transformation.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json
import unittest

from flask import Flask
from marshmallow import fields
from werkzeug.exceptions import BadRequest
from unittest.mock import ANY
from unittest.mock import patch
from tests.helpers import make_test_response

from flask_rebar import messages, validation, response, Rebar
from flask_rebar import errors
from flask_rebar.utils.request_utils import get_json_body_params_or_400
from flask_rebar.utils.request_utils import get_query_string_params_or_400


class TestErrors(unittest.TestCase):
    ERROR_MSG = messages.ErrorMessage(
        "Bamboozled!", messages.ErrorCode.INTERNAL_SERVER_ERROR
    )

    def setUp(self):
        self.app = self.create_app()
        self.app.response_class = make_test_response(self.app.response_class)

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

        @app.route("/slow", methods=["GET"])
        def a_slow_handler():
            raise SystemExit()

        Rebar().init_app(app=app)

        return app

    def test_custom_http_errors_are_handled(self):
        resp = self.app.test_client().get("/errors")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content_type, "application/json")
        self.assertEqual(resp.json, TestErrors.ERROR_MSG._asdict())

    def test_custom_http_errors_can_have_additional_data(self):
        resp = self.app.test_client().get("/verbose_errors")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content_type, "application/json")
        expected = TestErrors.ERROR_MSG._asdict()
        expected["foo"] = "bar"
        self.assertEqual(resp.json, expected)

    def test_customize_rebar_error_attribute(self):
        rebar = self.app.extensions["rebar"]["instance"]
        # option 1: supply custom name for attribute in response
        rebar.error_code_attr = "xyz123"
        resp = self.app.test_client().get("/errors")
        expected = TestErrors.ERROR_MSG._asdict()
        expected["xyz123"] = expected.pop("rebar_error_code")
        self.assertEqual(resp.json, expected)

        # option 2: suppress rebar-internal error codes entirely
        rebar.error_code_attr = None
        resp = self.app.test_client().get("/errors")
        expected = TestErrors.ERROR_MSG._asdict()
        expected.pop("rebar_error_code")
        self.assertEqual(resp.json, expected)

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
        self.assertEqual(resp.json, messages.internal_server_error._asdict())

    def test_timeouts_log_exceptions(self):
        # in the wild, gunicorn or nginx will cutoff the wsgi server and return a 502
        # causing the wsgi server to raise SystemExit
        with patch.object(self.app.logger, "error") as mock_logger, self.assertRaises(
            SystemExit
        ):
            self.app.test_client().get("/slow")
            mock_logger.error.assert_called_with(
                "Exception on /slow [GET]", exc_info=ANY
            )


class TestJsonBodyValidation(unittest.TestCase):
    def setUp(self):
        self.app = self.create_app()
        self.app.response_class = make_test_response(self.app.response_class)

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
        self.assertEqual(resp.json, messages.empty_json_body._asdict())

        resp = self.app.test_client().post(
            path="/stuffs",
            data=json.dumps({"foo": 1}),
            headers={"Content-Type": "text/csv"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, messages.unsupported_content_type._asdict())

        resp = self.app.test_client().post(
            path="/stuffs",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, messages.invalid_json._asdict())

    def test_json_body_parameter_validation(self):
        # Only field errors
        resp = self.post_json(
            path="/stuffs", data={"foo": "one", "bar": "not-an-email"}
        )
        expected = messages.body_validation_failed._asdict()
        expected["errors"] = {
            "foo": "Not a valid integer.",
            "bar": "Not a valid email address.",
        }

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, expected)

        # Only general errors
        resp = self.post_json(
            path="/stuffs", data={"foo": 1, "baz": "This is an unexpected field!"}
        )
        expected = messages.body_validation_failed._asdict()
        expected["errors"] = {"baz": "Unknown field."}

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, expected)

        # Both field errors and general errors
        resp = self.post_json(
            path="/stuffs", data={"baz": "This is an unexpected field!"}
        )
        self.assertEqual(resp.status_code, 400)
        expected = messages.body_validation_failed._asdict()
        expected["errors"] = {
            "baz": "Unknown field.",
            "foo": "Missing data for required field.",
        }

        self.assertEqual(resp.json, expected)

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
        expected = messages.body_validation_failed._asdict()
        expected["errors"] = {
            "bam": "Unknown field.",
            "foo": "Missing data for required field.",
            "nested": {
                "unexpected": "Unknown field.",
                "baz": {"0": "Not a valid integer.", "1": "Not a valid integer."},
            },
        }

        self.assertEqual(resp.status_code, 400)

        self.assertEqual(resp.json, expected)

    def test_invalid_json_error(self):
        resp = self.app.test_client().post(
            path="/stuffs",
            data='"Im technically valid JSON, but not an object"',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, messages.invalid_json._asdict())


class TestQueryStringValidation(unittest.TestCase):
    def setUp(self):
        self.app = self.create_app()
        self.app.response_class = make_test_response(self.app.response_class)

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
        expected = messages.query_string_validation_failed._asdict()
        expected["errors"] = {"foo": "Not a valid integer."}
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, expected)

        resp = self.app.test_client().get(path="/stuffs?bar=true")
        expected = messages.query_string_validation_failed._asdict()
        expected["errors"] = {"foo": "Missing data for required field."}

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, expected)

        resp = self.app.test_client().get(path="/stuffs?foo=1&unexpected=true")
        expected = messages.query_string_validation_failed._asdict()
        expected["errors"] = {"unexpected": "Unknown field."}

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, expected)

        resp = self.app.test_client().get(path="/stuffs?foo=1&bar=true&baz=1,2,3")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"foo": 1, "bar": True, "baz": [1, 2, 3]})
