from __future__ import unicode_literals

import json

import flask
from marshmallow import fields
import pytest
from werkzeug.exceptions import BadRequest
from werkzeug.utils import cached_property

from flask_rebar import errors
from flask_rebar import Rebar
from flask_rebar import response
from flask_rebar import validation
from flask_rebar.utils.request_utils import get_json_body_params_or_400
from flask_rebar.utils.request_utils import get_query_string_params_or_400


class JSONResponse(object):
    """Mixin with testing helper methods for JSON responses.
    required for older versions of flask.
    """

    @cached_property
    def json(self):
        """Try to deserialize response data (a string containing a valid JSON
        document) to a Python object by passing it to the underlying
        :mod:`flask.json` module.
        """
        return json.loads(self.data)

    def __eq__(self, other):
        if isinstance(other, int):
            return self.status_code == other
        # even though the Python 2-specific code works on Python 3, keep the two versions
        # separate so we can simplify the code once Python 2 support is dropped
        if sys.version_info[0] == 2:
            try:
                super_eq = super(JSONResponse, self).__eq__
            except AttributeError:
                return NotImplemented
            else:
                return super_eq(other)
        else:
            return super(JSONResponse, self).__eq__(other)

    def __ne__(self, other):
        return not self == other


@pytest.fixture
def app():
    obj = flask.Flask(__name__)
    if not hasattr(obj.response_class, 'json'):
        obj.response_class = type(
            str(JSONResponse),
            (obj.response_class, JSONResponse),
            {},
        )  # create new json object type
    return obj


@pytest.fixture
def error_msg():
    return "Bamboozled!"


@pytest.fixture
def error_app(app, error_msg):
    @app.route("/errors", methods=["GET"])
    def a_terrible_handler():
        raise errors.Conflict(msg=error_msg)

    @app.route("/uncaught_errors", methods=["GET"])
    def an_even_worse_handler():
        raise ArithmeticError()

    @app.route("/verbose_errors", methods=["GET"])
    def a_fancy_handler():
        raise errors.Conflict(msg=error_msg, additional_data={"foo": "bar"})

    @app.route("/route_that_fails_validation", methods=["GET"])
    def validation_fails_handler():
        raise BadRequest()

    @app.route("/slow", methods=["GET"])
    def a_slow_handler():
        raise SystemExit()

    Rebar().init_app(app=app)

    return app


@pytest.fixture
def json_body_app(app):
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


@pytest.fixture
def post_json(json_body_app):
    def func(path, data):
        return json_body_app.test_client().post(
            path=path,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

    return func


@pytest.fixture
def query_string_app(app):
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
