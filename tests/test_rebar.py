"""
    Test Rebar
    ~~~~~~~~~~

    Tests for the basic usage of Flask-Rebar.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json
import unittest

import marshmallow as m
from flask import Flask
from werkzeug.routing import RequestRedirect

from flask_rebar import HeaderApiKeyAuthenticator, SwaggerV3Generator
from flask_rebar.authenticators import USE_DEFAULT
from flask_rebar import messages
from flask_rebar.compat import set_data_key
from flask_rebar.rebar import Rebar
from flask_rebar.rebar import prefix_url
from flask_rebar.testing import validate_swagger
from flask_rebar.testing.swagger_jsonschema import SWAGGER_V3_JSONSCHEMA

DEFAULT_AUTH_HEADER = "x-default-auth"
DEFAULT_AUTH_SECRET = "SECRET!"
DEFAULT_RESPONSE = {"uid": "0", "name": "I'm the default for testing!"}
DEFAULT_ERROR = {"message": messages.internal_server_error}


class FooSchema(m.Schema):
    uid = m.fields.String()
    name = m.fields.String()


class ListOfFooSchema(m.Schema):
    data = m.fields.Nested(FooSchema, many=True)


class FooUpdateSchema(m.Schema):
    name = m.fields.String()


class FooListSchema(m.Schema):
    name = m.fields.String(required=True)


class HeadersSchema(m.Schema):
    name = set_data_key(
        field=m.fields.String(load_from="x-name", required=True), key="x-name"
    )


class MeSchema(m.Schema):
    user_name = m.fields.String()


def get_json_from_resp(resp):
    return json.loads(resp.data.decode("utf-8"))


def get_swagger(test_client, prefix=None):
    url = "/swagger"
    if prefix:
        url = prefix_url(prefix=prefix, url=url)
    return get_json_from_resp(test_client.get(url))


def auth_headers(header=DEFAULT_AUTH_HEADER, secret=DEFAULT_AUTH_SECRET):
    return dict([(header, secret)])


def create_rebar_app(rebar):
    app = Flask("RebarTest")
    app.testing = True
    rebar.init_app(app)
    return app


def register_default_authenticator(registry):
    default_authenticator = HeaderApiKeyAuthenticator(
        header=DEFAULT_AUTH_HEADER, name="default"
    )
    default_authenticator.register_key(app_name="internal", key=DEFAULT_AUTH_SECRET)
    registry.set_default_authenticator(default_authenticator)


def register_endpoint(
    registry,
    func=None,
    path="/foos/<foo_uid>",
    method="GET",
    endpoint=None,
    response_body_schema=None,
    query_string_schema=None,
    request_body_schema=None,
    headers_schema=None,
    authenticator=USE_DEFAULT,
):
    def default_handler_func(*args, **kwargs):
        return DEFAULT_RESPONSE

    registry.add_handler(
        func=func or default_handler_func,
        rule=path,
        method=method,
        endpoint=endpoint,
        response_body_schema=response_body_schema or {200: FooSchema()},
        query_string_schema=query_string_schema,
        request_body_schema=request_body_schema,
        headers_schema=headers_schema,
        authenticator=authenticator,
    )


class RebarTest(unittest.TestCase):
    def test_default_authentication(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        register_default_authenticator(registry)
        register_endpoint(registry)
        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1", headers=auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().get(
            path="/foos/1", headers=auth_headers(secret="LIES!")
        )
        self.assertEqual(resp.status_code, 401)

    def test_override_authenticator(self):
        auth_header = "x-overridden-auth"
        auth_secret = "BLAM!"

        rebar = Rebar()
        registry = rebar.create_handler_registry()

        register_default_authenticator(registry)
        authenticator = HeaderApiKeyAuthenticator(header=auth_header)
        authenticator.register_key(app_name="internal", key=auth_secret)

        register_endpoint(registry, authenticator=authenticator)
        app = create_rebar_app(rebar)

        resp = app.test_client().get(
            path="/foos/1", headers=auth_headers(header=auth_header, secret=auth_secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        # The default authentication doesn't work anymore!
        resp = app.test_client().get(path="/foos/1", headers=auth_headers())
        self.assertEqual(resp.status_code, 401)

    def test_override_with_no_authenticator(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        register_default_authenticator(registry)
        register_endpoint(registry, authenticator=None)
        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

    def test_validate_body_parameters(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(
            rule="/foos/<foo_uid>",
            method="PATCH",
            response_body_schema={200: FooSchema()},
            request_body_schema=FooUpdateSchema(),
        )
        def update_foo(foo_uid):
            return {"uid": foo_uid, "name": rebar.validated_body["name"]}

        app = create_rebar_app(rebar)

        resp = app.test_client().patch(
            path="/foos/1",
            data=json.dumps({"name": "jill"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), {"uid": "1", "name": "jill"})

        resp = app.test_client().patch(
            path="/foos/1",
            data=json.dumps({"name": 123}),  # Name should be string, not int
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_validate_query_parameters(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(
            rule="/foos",
            method="GET",
            response_body_schema={200: ListOfFooSchema()},
            query_string_schema=FooListSchema(),
        )
        def list_foos():
            return {"data": [{"name": rebar.validated_args["name"], "uid": "1"}]}

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos?name=jill")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            get_json_from_resp(resp), {"data": [{"uid": "1", "name": "jill"}]}
        )

        resp = app.test_client().get(path="/foos?foo=bar")  # missing required parameter
        self.assertEqual(resp.status_code, 400)

    def test_validate_headers(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        register_default_authenticator(registry)

        @registry.handles(
            rule="/me",
            method="GET",
            response_body_schema={200: MeSchema()},
            headers_schema=HeadersSchema(),
        )
        def get_me():
            return {"user_name": rebar.validated_headers["name"]}

        app = create_rebar_app(rebar)

        headers = auth_headers()
        headers["x-name"] = "hello"

        resp = app.test_client().get(path="/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), {"user_name": "hello"})

        resp = app.test_client().get(
            path="/me", headers=auth_headers()  # Missing the x-name header!
        )
        self.assertEqual(resp.status_code, 400)

    def test_default_mimetype_for_null_response_schema(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry(default_mimetype="content/type")

        @registry.handles(rule="/me", method="DELETE", response_body_schema={204: None})
        def delete_me():
            return None, 204

        app = create_rebar_app(rebar)
        resp = app.test_client().delete(path="/me")

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.data.decode("utf-8"), "")
        self.assertEqual(resp.headers["Content-Type"], "content/type")

    def test_default_mimetype_for_non_null_response_schema(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry(default_mimetype="content/type")

        @registry.handles(
            rule="/me", method="DELETE", response_body_schema={204: m.Schema()}
        )
        def delete_me():
            return {}, 204

        app = create_rebar_app(rebar)
        resp = app.test_client().delete(path="/me")

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.data.decode("utf-8"), "")
        self.assertEqual(resp.headers["Content-Type"], "content/type")

    def test_handler_mimetype_for_null_response_schema(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(
            rule="/me",
            method="DELETE",
            response_body_schema={204: None},
            mimetype="content/type",
        )
        def delete_me():
            return None, 204

        app = create_rebar_app(rebar)
        resp = app.test_client().delete(path="/me")

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.data.decode("utf-8"), "")
        self.assertEqual(resp.headers["Content-Type"], "content/type")

    def test_handler_mimetype_for_non_null_response_schema(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(
            rule="/me",
            method="DELETE",
            response_body_schema={204: m.Schema()},
            mimetype="content/type",
        )
        def delete_me():
            return {}, 204

        app = create_rebar_app(rebar)
        resp = app.test_client().delete(path="/me")

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.data.decode("utf-8"), "")
        self.assertEqual(resp.headers["Content-Type"], "content/type")

    def test_handler_mimetype_overrides_default_mimetype(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry(default_mimetype="default/type")

        @registry.handles(
            rule="/me",
            method="DELETE",
            response_body_schema={204: m.Schema()},
            mimetype="handler/type",
        )
        def delete_me():
            return {}, 204

        app = create_rebar_app(rebar)
        resp = app.test_client().delete(path="/me")

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.data.decode("utf-8"), "")
        self.assertEqual(resp.headers["Content-Type"], "handler/type")

    def test_view_function_tuple_response(self):
        header_key = "X-Foo"
        header_value = "bar"
        headers = {header_key: header_value}

        for (
            response_body_schema,
            rv,
            expected_status,
            expected_body,
            expected_headers,
        ) in [
            (FooSchema(), DEFAULT_RESPONSE, 200, DEFAULT_RESPONSE, {}),
            ({201: FooSchema()}, (DEFAULT_RESPONSE, 201), 201, DEFAULT_RESPONSE, {}),
            ({201: FooSchema()}, (DEFAULT_RESPONSE, 200), 500, DEFAULT_ERROR, {}),
            ({204: None}, (None, 204), 204, "", {}),
            (
                {200: FooSchema()},
                (DEFAULT_RESPONSE, headers),
                200,
                DEFAULT_RESPONSE,
                headers,
            ),
            (
                {201: FooSchema()},
                (DEFAULT_RESPONSE, 201, headers),
                201,
                DEFAULT_RESPONSE,
                headers,
            ),
            ({201: None}, (None, 201, headers), 201, "", headers),
            ({201: FooSchema()}, ({}, 201, headers), 201, {}, headers),
        ]:
            rebar = Rebar()
            registry = rebar.create_handler_registry()

            @registry.handles(rule="/foo", response_body_schema=response_body_schema)
            def foo():
                return rv

            app = create_rebar_app(rebar)

            resp = app.test_client().get("/foo")

            body = get_json_from_resp(resp) if resp.data else resp.data.decode()
            self.assertEqual(body, expected_body)
            self.assertEqual(resp.status_code, expected_status)

            for key, value in expected_headers.items():
                self.assertEqual(resp.headers[key], value)

    def test_swagger_endpoint_is_automatically_created(self):
        rebar = Rebar()
        rebar.create_handler_registry()
        app = create_rebar_app(rebar)

        resp = app.test_client().get("/swagger")

        self.assertEqual(resp.status_code, 200)

        validate_swagger(get_json_from_resp(resp))

    def test_swagger_ui_endpoint_is_automatically_created(self):
        rebar = Rebar()
        rebar.create_handler_registry()
        app = create_rebar_app(rebar)

        resp = app.test_client().get("/swagger/ui/")
        self.assertEqual(resp.status_code, 200)

    def test_swagger_ui_without_trailing_slash(self):
        rebar = Rebar()
        rebar.create_handler_registry()
        app = create_rebar_app(rebar)

        resp = app.test_client().get("/swagger/ui")
        self.assertEqual(resp.status_code, 200)

    def test_swagger_can_be_set_to_v3(self):
        rebar = Rebar()
        rebar.create_handler_registry(swagger_generator=SwaggerV3Generator())
        app = create_rebar_app(rebar)

        resp = app.test_client().get("/swagger")
        self.assertEqual(resp.status_code, 200)
        validate_swagger(get_json_from_resp(resp), SWAGGER_V3_JSONSCHEMA)

        resp = app.test_client().get("/swagger/ui/")
        self.assertEqual(resp.status_code, 200)

    def test_register_multiple_paths(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        common_kwargs = {"method": "GET", "response_body_schema": {200: FooSchema()}}

        @registry.handles(rule="/bars/<foo_uid>", endpoint="bar", **common_kwargs)
        @registry.handles(rule="/foos/<foo_uid>", endpoint="foo", **common_kwargs)
        def handler_func(foo_uid):
            return DEFAULT_RESPONSE

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().get(path="/bars/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        swagger = get_swagger(test_client=app.test_client())
        self.assertIn("/bars/{foo_uid}", swagger["paths"])
        self.assertIn("/foos/{foo_uid}", swagger["paths"])

    def test_register_multiple_methods(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        common_kwargs = {
            "rule": "/foos/<foo_uid>",
            "response_body_schema": {200: FooSchema()},
        }

        @registry.handles(method="GET", endpoint="get_foo", **common_kwargs)
        @registry.handles(method="PATCH", endpoint="update_foo", **common_kwargs)
        def handler_func(foo_uid):
            return DEFAULT_RESPONSE

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().patch(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().post(path="/foos/1")
        self.assertEqual(resp.status_code, 405)

        swagger = get_swagger(test_client=app.test_client())
        self.assertIn("get", swagger["paths"]["/foos/{foo_uid}"])
        self.assertIn("patch", swagger["paths"]["/foos/{foo_uid}"])

    def test_default_headers(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        registry.set_default_headers_schema(HeadersSchema())

        @registry.handles(rule="/me", method="GET", response_body_schema=MeSchema())
        def get_me():
            return {"user_name": rebar.validated_headers["name"]}

        @registry.handles(
            rule="/myself",
            method="GET",
            response_body_schema=MeSchema(),
            # Let's make sure this can be overridden
            headers_schema=None,
        )
        def get_myself():
            return DEFAULT_RESPONSE

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/me", headers={"x-name": "hello"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), {"user_name": "hello"})

        resp = app.test_client().get(path="/me")
        self.assertEqual(resp.status_code, 400)

        resp = app.test_client().get(path="/myself")
        self.assertEqual(resp.status_code, 200)

        swagger = get_swagger(test_client=app.test_client())
        self.assertEqual(
            swagger["paths"]["/me"]["get"]["parameters"][0]["name"], "x-name"
        )
        self.assertNotIn("parameters", swagger["paths"]["/myself"]["get"])

    def test_swagger_endpoints_can_be_omitted(self):
        rebar = Rebar()
        rebar.create_handler_registry(swagger_path=None, swagger_ui_path=None)
        app = create_rebar_app(rebar)

        resp = app.test_client().get("/swagger")
        self.assertEqual(resp.status_code, 404)

        resp = app.test_client().get("/swagger/ui")
        self.assertEqual(resp.status_code, 404)

    def test_rebar_can_be_url_prefixed(self):
        app = Flask(__name__)
        app.testing = True

        rebar = Rebar()
        registry_v1 = rebar.create_handler_registry(prefix="v1")
        registry_v2 = rebar.create_handler_registry(
            prefix="/v2/"
        )  # Slashes shouldn't matter

        # We use the same endpoint to show that the swagger operationId gets set correctly
        # and the Flask endpoint gets prefixed
        register_endpoint(registry=registry_v1, endpoint="get_foo")
        register_endpoint(registry=registry_v2, endpoint="get_foo")

        rebar.init_app(app)

        for prefix in ("v1", "v2"):
            resp = app.test_client().get(prefix_url(prefix=prefix, url="/swagger/ui/"))
            self.assertEqual(resp.status_code, 200)

            swagger = get_swagger(test_client=app.test_client(), prefix=prefix)
            validate_swagger(swagger)

            self.assertEqual(
                swagger["paths"][prefix_url(prefix=prefix, url="/foos/{foo_uid}")][
                    "get"
                ]["operationId"],
                "get_foo",
            )
            resp = app.test_client().get(prefix_url(prefix=prefix, url="/foos/1"))
            self.assertEqual(resp.status_code, 200)

    def test_clone_rebar(self):
        rebar = Rebar()
        app = Flask(__name__)
        app.testing = True

        registry = rebar.create_handler_registry()

        register_default_authenticator(registry)
        register_endpoint(registry)

        cloned = registry.clone()
        cloned.prefix = "v1"
        rebar.add_handler_registry(registry=cloned)

        rebar.init_app(app)

        resp = app.test_client().get("/swagger/ui/")
        self.assertEqual(resp.status_code, 200)

        resp = app.test_client().get(path="/foos/1", headers=auth_headers())
        self.assertEqual(resp.status_code, 200)

        resp = app.test_client().get("/v1/swagger/ui/")
        self.assertEqual(resp.status_code, 200)

        resp = app.test_client().get(path="/v1/foos/1", headers=auth_headers())
        self.assertEqual(resp.status_code, 200)

    def test_uncaught_errors_are_not_jsonified_in_debug_mode(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles("/force_500")
        def force_500():
            raise ArithmeticError()

        app = create_rebar_app(rebar)

        app.debug = False
        resp = app.test_client().get(path="/force_500")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content_type, "application/json")

        app.debug = True
        with self.assertRaises(ArithmeticError):
            app.test_client().get(path="/force_500")

    def test_redirects_for_missing_trailing_slash(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        register_endpoint(registry=registry, path="/with_trailing_slash/")

        app = create_rebar_app(rebar)

        app.debug = False
        resp = app.test_client().get(path="/with_trailing_slash")
        self.assertIn(resp.status_code, (301, 308))
        self.assertTrue(resp.headers["Location"].endswith("/with_trailing_slash/"))

        app.debug = True
        resp = app.test_client().get(path="/with_trailing_slash")
        self.assertIn(resp.status_code, (301, 308))
        self.assertTrue(resp.headers["Location"].endswith("/with_trailing_slash/"))
