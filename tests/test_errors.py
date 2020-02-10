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
from marshmallow import fields
from werkzeug.exceptions import BadRequest
from mock import ANY
from mock import patch
import pytest

from flask_rebar import messages, validation, response
from flask_rebar.compat import MARSHMALLOW_V2
from flask_rebar import errors


def test_custom_http_errors_are_handled(error_app, error_msg):
    resp = error_app.test_client().get("/errors")
    assert resp.status_code == 409
    assert resp.content_type == "application/json"
    assert resp.json == {"message": error_msg}


def test_custom_http_errors_can_have_additional_data(error_app, error_msg):
    resp = error_app.test_client().get("/verbose_errors")
    assert resp.status_code == 409
    assert resp.content_type == "application/json"
    assert resp.json == {"message": error_msg, "foo": "bar"}


def test_default_400_errors_are_formatted_correctly(error_app, error_msg):
    resp = error_app.test_client().get("/route_that_fails_validation")
    assert resp.status_code == 400
    assert resp.content_type == "application/json"
    assert resp.json.get("message")


def test_default_404_errors_are_formatted_correctly(error_app):
    resp = error_app.test_client().get("/nonexistent")
    assert resp.status_code == 404
    assert resp.content_type == "application/json"
    assert resp.json.get("message")


def test_default_405_errors_are_formatted_correctly(error_app):
    resp = error_app.test_client().put("/errors")
    assert resp.status_code == 405
    assert resp.content_type == "application/json"
    resp.json.get("message")


def test_default_500_errors_are_formatted_correctly(error_app):
    resp = error_app.test_client().get("/uncaught_errors")
    assert resp.status_code == 500
    assert resp.content_type == "application/json"
    assert resp.json == {"message": messages.internal_server_error}


def test_timeouts_log_exceptions(error_app):
    # in the wild, gunicorn or nginx will cutoff the wsgi server and return a 502
    # causing the wsgi server to raise SystemExit
    with patch.object(error_app.logger, "error") as mock_logger, pytest.raises(
        SystemExit
    ):
        error_app.test_client().get("/slow")
        mock_logger.error.assert_called_with("Exception on /slow [GET]", exc_info=ANY)


def test_json_encoding_validation(json_body_app):
    resp = json_body_app.test_client().post(
        path="/stuffs", headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 400
    assert resp.json == {"message": messages.empty_json_body}

    resp = json_body_app.test_client().post(
        path="/stuffs",
        data=json.dumps({"foo": 1}),
        headers={"Content-Type": "text/csv"},
    )
    assert resp.status_code == 400
    assert resp.json == {"message": messages.unsupported_content_type}

    resp = json_body_app.test_client().post(
        path="/stuffs",
        data="not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json == {"message": messages.invalid_json}


def test_json_body_parameter_validation(post_json):
    # Only field errors
    resp = post_json(path="/stuffs", data={"foo": "one", "bar": "not-an-email"})
    assert resp.status_code == 400
    assert resp.json == {
        "message": messages.body_validation_failed,
        "errors": {"foo": "Not a valid integer.", "bar": "Not a valid email address."},
    }

    # Only general errors
    resp = post_json(
        path="/stuffs", data={"foo": 1, "baz": "This is an unexpected field!"}
    )
    assert resp.status_code == 400
    if MARSHMALLOW_V2:
        assert resp.json == {
            "message": messages.body_validation_failed,
            "errors": {"_general": "Unexpected field: baz"},
        }
    else:
        assert resp.json == {
            "message": messages.body_validation_failed,
            "errors": {"baz": "Unknown field."},
        }

    # Both field errors and general errors
    resp = post_json(path="/stuffs", data={"baz": "This is an unexpected field!"})
    assert resp.status_code == 400

    if MARSHMALLOW_V2:
        assert resp.json == {
            "message": messages.body_validation_failed,
            "errors": {
                "_general": "Unexpected field: baz",
                "foo": "Missing data for required field.",
            },
        }
    else:
        assert resp.json == {
            "message": messages.body_validation_failed,
            "errors": {
                "baz": "Unknown field.",
                "foo": "Missing data for required field.",
            },
        }

    # Happy path
    resp = post_json(path="/stuffs", data={"foo": 1})
    assert resp.status_code == 200


def test_representing_complex_errors(post_json):
    resp = post_json(
        path="/stuffs",
        data={
            "bam": "wow!",
            "nested": {"baz": ["one", "two"], "unexpected": "surprise!"},
        },
    )
    assert resp.status_code == 400

    if MARSHMALLOW_V2:
        assert resp.json == {
            "message": messages.body_validation_failed,
            "errors": {
                "_general": "Unexpected field: bam",
                "foo": "Missing data for required field.",
                "nested": {
                    "_general": "Unexpected field: unexpected",
                    "baz": {"0": "Not a valid integer.", "1": "Not a valid integer."},
                },
            },
        }
    else:
        assert resp.json == {
            "message": messages.body_validation_failed,
            "errors": {
                "bam": "Unknown field.",
                "foo": "Missing data for required field.",
                "nested": {
                    "unexpected": "Unknown field.",
                    "baz": {"0": "Not a valid integer.", "1": "Not a valid integer."},
                },
            },
        }


def test_invalid_json_error(json_body_app):
    resp = json_body_app.test_client().post(
        path="/stuffs",
        data='"Im technically valid JSON, but not an object"',
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json == {"message": messages.invalid_json}


def test_query_string_parameter_validation(query_string_app):
    resp = query_string_app.test_client().get(path="/stuffs?foo=one")
    assert resp.status_code == 400
    assert resp.json == {
        "message": messages.query_string_validation_failed,
        "errors": {"foo": "Not a valid integer."},
    }

    resp = query_string_app.test_client().get(path="/stuffs?bar=true")
    assert resp.status_code == 400
    assert resp.json == {
        "message": messages.query_string_validation_failed,
        "errors": {"foo": "Missing data for required field."},
    }

    resp = query_string_app.test_client().get(path="/stuffs?foo=1&unexpected=true")
    assert resp.status_code == 400
    if MARSHMALLOW_V2:
        assert resp.json == {
            "message": messages.query_string_validation_failed,
            "errors": {"_general": "Unexpected field: unexpected"},
        }
    else:
        assert resp.json == {
            "message": messages.query_string_validation_failed,
            "errors": {"unexpected": "Unknown field."},
        }

    resp = query_string_app.test_client().get(path="/stuffs?foo=1&bar=true&baz=1,2,3")
    assert resp.status_code == 200
    assert resp.json == {"foo": 1, "bar": True, "baz": [1, 2, 3]}
