"""
    Test Request Utilities
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests for the request utilities.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from marshmallow import fields, ValidationError
import pytest

from flask_rebar import validation, response, marshal


def test_single_resource_response(app):
    @app.route("/single_resource")
    def handler():
        return response(data={"foo": "bar"})

    resp = app.test_client().get("/single_resource")
    assert resp.status_code == 200
    assert resp.json == {"foo": "bar"}
    assert resp.content_type == "application/json"


def test_single_resource_response_with_status_code(app):
    @app.route("/single_resource")
    def handler():
        return response(data={"foo": "bar"}, status_code=201)

    resp = app.test_client().get("/single_resource")
    assert resp.status_code == 201
    assert resp.json == {"foo": "bar"}
    assert resp.content_type == "application/json"


def test_single_resource_response_with_headers(app):
    header_key = "X-Foo"
    header_value = "bar"

    @app.route("/single_resource")
    def handler():
        return response(data={"foo": "bar"}, headers={header_key: header_value})

    resp = app.test_client().get("/single_resource")
    assert resp.headers[header_key] == header_value
    assert resp.json == {"foo": "bar"}
    assert resp.content_type == "application/json"


class SchemaForMarshaling(validation.ResponseSchema):
    foo = fields.Integer()


def test_marshal():
    marshaled = marshal(data={"foo": 1}, schema=SchemaForMarshaling)
    assert marshaled == {"foo": 1}

    # Also works with an instance of the schema
    marshaled = marshal(data={"foo": 1}, schema=SchemaForMarshaling())

    assert marshaled == {"foo": 1}


def test_marshal_errors():
    with pytest.raises(ValidationError):
        marshal(data={"foo": "bar"}, schema=SchemaForMarshaling)
