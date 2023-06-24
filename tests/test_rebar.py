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
import marshmallow_objects as mo
from flask import Flask, make_response

from parametrize import parametrize

from flask_rebar import messages
from flask_rebar import HeaderApiKeyAuthenticator, SwaggerV3Generator
from flask_rebar.compat import set_data_key
from flask_rebar.rebar import Rebar
from flask_rebar.rebar import prefix_url
from flask_rebar.testing import validate_swagger
from flask_rebar.utils.defaults import USE_DEFAULT
from flask_rebar.testing.swagger_jsonschema import SWAGGER_V3_JSONSCHEMA

DEFAULT_AUTH_HEADER = "x-default-auth"
DEFAULT_AUTH_SECRET = "SECRET!"
DEFAULT_ALTERNATIVE_AUTH_HEADER = "x-api-default-auth"
DEFAULT_ALTERNATIVE_AUTH_SECRET = "ALSO A SECRET!"
DEFAULT_RESPONSE = {"uid": "0", "name": "I'm the default for testing!"}
DEFAULT_ERROR = (
    messages.internal_server_error._asdict()  # noqa - _asdict is NOT internal.
)


class FooSchema(m.Schema):
    uid = m.fields.String()
    name = m.fields.String()


class FooModel(mo.Model):
    uid = mo.fields.String()
    name = mo.fields.String()


class ListOfFooSchema(m.Schema):
    data = m.fields.Nested(FooSchema, many=True)


class ListOfFooModel(mo.Model):
    data = mo.NestedModel(FooModel, many=True)


class FooUpdateSchema(m.Schema):
    name = m.fields.String()


class FooUpdateModel(mo.Model):
    name = mo.fields.String()


class FooListSchema(m.Schema):
    name = m.fields.String(required=True)


class FooListModel(mo.Model):
    name = mo.fields.String(required=True)


class HeadersSchema(m.Schema):
    name = set_data_key(field=m.fields.String(required=True), key="x-name")


class HeadersModel(mo.Model):
    name = set_data_key(field=mo.fields.String(required=True), key="x-name")


class MeSchema(m.Schema):
    user_name = m.fields.String()


class DefaultResponseSchema(
    m.Schema
):  # DEFAULT_RESPONSE = {"uid": "0", "name": "I'm the default for testing!"}
    uid = m.fields.String()
    name = m.fields.String()


def get_swagger(test_client, prefix=None):
    url = "/swagger"
    if prefix:
        url = prefix_url(prefix=prefix, url=url)
    return test_client.get(url).json


def auth_headers(header=DEFAULT_AUTH_HEADER, secret=DEFAULT_AUTH_SECRET):
    return dict([(header, secret)])


def alternative_auth_headers(
    header=DEFAULT_ALTERNATIVE_AUTH_HEADER, secret=DEFAULT_ALTERNATIVE_AUTH_SECRET
):
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


def register_multiple_authenticators(registry):
    default_authenticator = HeaderApiKeyAuthenticator(
        header=DEFAULT_AUTH_HEADER, name="default"
    )
    default_authenticator.register_key(app_name="internal", key=DEFAULT_AUTH_SECRET)
    alternative_default_authenticator = HeaderApiKeyAuthenticator(
        header=DEFAULT_ALTERNATIVE_AUTH_HEADER, name="alternative"
    )
    alternative_default_authenticator.register_key(
        app_name="internal", key=DEFAULT_ALTERNATIVE_AUTH_SECRET
    )
    registry.set_default_authenticators(
        (default_authenticator, alternative_default_authenticator)
    )


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
    authenticators=USE_DEFAULT,
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
        authenticators=authenticators,
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
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        resp = app.test_client().get(
            path="/foos/1", headers=auth_headers(secret="LIES!")
        )
        self.assertEqual(resp.status_code, 401)

    def test_default_authentication_w_multiple(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        register_multiple_authenticators(registry)
        register_endpoint(registry)
        app = create_rebar_app(rebar)

        # Test main
        resp = app.test_client().get(path="/foos/1", headers=auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        # Test alternative
        resp = app.test_client().get(path="/foos/1", headers=alternative_auth_headers())
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

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

        register_endpoint(registry, authenticators=authenticator)
        app = create_rebar_app(rebar)

        resp = app.test_client().get(
            path="/foos/1", headers=auth_headers(header=auth_header, secret=auth_secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        # The default authentication doesn't work anymore!
        resp = app.test_client().get(path="/foos/1", headers=auth_headers())
        self.assertEqual(resp.status_code, 401)

    def test_override_with_no_authenticator(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        register_default_authenticator(registry)
        register_endpoint(registry, authenticators=None)
        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

    @parametrize(
        "foo_cls,foo_update_cls,use_model",
        [(FooSchema, FooUpdateSchema, False), (FooModel, FooUpdateModel, True)],
    )
    def test_validate_body_parameters(self, foo_cls, foo_update_cls, use_model):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(
            rule="/foos/<foo_uid>",
            method="PATCH",
            response_body_schema={200: foo_cls()},
            request_body_schema=foo_update_cls(),
        )
        def update_foo(foo_uid):
            if use_model:
                # Here we can also verify that in handler we get our expected FooModel type object
                self.assertIsInstance(rebar.validated_body, foo_update_cls)
                return foo_cls(name=rebar.validated_body.name, uid=foo_uid)
            else:
                return {"uid": foo_uid, "name": rebar.validated_body["name"]}

        app = create_rebar_app(rebar)

        resp = app.test_client().patch(
            path="/foos/1",
            data=json.dumps({"name": "jill"}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"uid": "1", "name": "jill"})

        resp = app.test_client().patch(
            path="/foos/1",
            data=json.dumps({"name": 123}),  # Name should be string, not int
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)

    @parametrize("foo_update_cls", [(FooUpdateSchema,), (FooUpdateModel,)])
    def test_flask_response_instance_interop_body_matches_schema(self, foo_update_cls):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        schema = foo_update_cls()

        @registry.handles(rule="/foo", method="PUT", response_body_schema=schema)
        def foo():
            return make_response((json.dumps({"name": "foo"}), {"foo": "bar"}))

        app = create_rebar_app(rebar)
        resp = app.test_client().put(path="/foo")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["foo"], "bar")

    @parametrize("foo_update_cls", [(FooUpdateSchema,), (FooUpdateModel,)])
    def test_flask_response_instance_interop_body_does_not_match_schema(
        self, foo_update_cls
    ):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        schema = foo_update_cls()

        @registry.handles(rule="/foo", method="PUT", response_body_schema=schema)
        def foo():
            return make_response(json.dumps({"does not match": "foo schema"}))

        app = create_rebar_app(rebar)
        resp = app.test_client().put(path="/foo")
        self.assertEqual(resp.status_code, 500)

    def test_flask_response_instance_interop_no_schema(self):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(rule="/foo", response_body_schema={302: None})
        def foo():
            return make_response(("Redirecting", 302, {"Location": "http://foo.com"}))

        app = create_rebar_app(rebar)
        resp = app.test_client().get(path="/foo")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], "http://foo.com")

    @parametrize("list_of_foo_cls", [(ListOfFooSchema,), (ListOfFooModel,)])
    def test_validate_query_parameters(self, list_of_foo_cls):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles(
            rule="/foos",
            method="GET",
            response_body_schema={200: list_of_foo_cls()},
            query_string_schema=FooListSchema(),
        )
        def list_foos():
            return {"data": [{"name": rebar.validated_args["name"], "uid": "1"}]}

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos?name=jill")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"data": [{"uid": "1", "name": "jill"}]})

        resp = app.test_client().get(path="/foos?foo=bar")  # missing required parameter
        self.assertEqual(resp.status_code, 400)

    @parametrize(
        "headers_cls, use_model", [(HeadersSchema, False), (HeadersModel, True)]
    )
    def test_validate_headers(self, headers_cls, use_model):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        register_default_authenticator(registry)

        @registry.handles(
            rule="/me",
            method="GET",
            response_body_schema={200: MeSchema()},
            headers_schema=headers_cls,
        )
        def get_me():
            name = (
                rebar.validated_headers.name
                if use_model
                else rebar.validated_headers["name"]
            )
            return {"user_name": name}

        app = create_rebar_app(rebar)

        headers = auth_headers()
        headers["x-name"] = "hello"

        resp = app.test_client().get(path="/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"user_name": "hello"})

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

    @parametrize("foo_definition", [(FooSchema,), (FooModel,)])
    def test_view_function_tuple_response(self, foo_definition):
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
            (foo_definition(), DEFAULT_RESPONSE, 200, DEFAULT_RESPONSE, {}),
            (
                {201: foo_definition()},
                (DEFAULT_RESPONSE, 201),
                201,
                DEFAULT_RESPONSE,
                {},
            ),
            ({201: foo_definition()}, (DEFAULT_RESPONSE, 200), 500, DEFAULT_ERROR, {}),
            ({204: None}, (None, 204), 204, "", {}),
            (
                {200: foo_definition()},
                (DEFAULT_RESPONSE, headers),
                200,
                DEFAULT_RESPONSE,
                headers,
            ),
            (
                {201: foo_definition()},
                (DEFAULT_RESPONSE, 201, headers),
                201,
                DEFAULT_RESPONSE,
                headers,
            ),
            ({201: None}, (None, 201, headers), 201, "", headers),
            ({201: foo_definition()}, ({}, 201, headers), 201, {}, headers),
        ]:
            rebar = Rebar()
            registry = rebar.create_handler_registry()

            @registry.handles(rule="/foo", response_body_schema=response_body_schema)
            def foo():
                return rv

            app = create_rebar_app(rebar)

            resp = app.test_client().get("/foo")

            body = resp.json if resp.data else resp.data.decode()
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

        validate_swagger(resp.json)

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
        validate_swagger(resp.json, SWAGGER_V3_JSONSCHEMA)

        resp = app.test_client().get("/swagger/ui/")
        self.assertEqual(resp.status_code, 200)

    @parametrize("foo_definition", [(FooSchema(),), (FooModel(),)])
    def test_register_multiple_paths(self, foo_definition):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        common_kwargs = {"method": "GET", "response_body_schema": {200: foo_definition}}

        @registry.handles(rule="/bars/<foo_uid>", endpoint="bar", **common_kwargs)
        @registry.handles(rule="/foos/<foo_uid>", endpoint="foo", **common_kwargs)
        def handler_func(foo_uid):
            return DEFAULT_RESPONSE

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        resp = app.test_client().get(path="/bars/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        swagger = get_swagger(test_client=app.test_client())
        self.assertIn("/bars/{foo_uid}", swagger["paths"])
        self.assertIn("/foos/{foo_uid}", swagger["paths"])

    @parametrize("foo_definition", [(FooSchema(),), (FooModel(),)])
    def test_register_multiple_methods(self, foo_definition):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        common_kwargs = {
            "rule": "/foos/<foo_uid>",
            "response_body_schema": {200: foo_definition},
        }

        @registry.handles(method="GET", endpoint="get_foo", **common_kwargs)
        @registry.handles(method="PATCH", endpoint="update_foo", **common_kwargs)
        def handler_func(foo_uid):
            return DEFAULT_RESPONSE

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        resp = app.test_client().patch(path="/foos/1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, DEFAULT_RESPONSE)

        resp = app.test_client().post(path="/foos/1")
        self.assertEqual(resp.status_code, 405)

        swagger = get_swagger(test_client=app.test_client())
        self.assertIn("get", swagger["paths"]["/foos/{foo_uid}"])
        self.assertIn("patch", swagger["paths"]["/foos/{foo_uid}"])

    @parametrize(
        "headers_def, use_model", [(HeadersSchema(), False), (HeadersModel, True)]
    )
    def test_default_headers(self, headers_def, use_model):
        rebar = Rebar()
        registry = rebar.create_handler_registry()
        registry.set_default_headers_schema(headers_def)

        @registry.handles(rule="/me", method="GET", response_body_schema=MeSchema())
        def get_me():
            name = (
                rebar.validated_headers.name
                if use_model
                else rebar.validated_headers["name"]
            )
            return {"user_name": name}

        @registry.handles(
            rule="/myself",
            method="GET",
            response_body_schema=DefaultResponseSchema(),
            # Let's make sure this can be overridden
            headers_schema=None,
        )
        def get_myself():
            return DEFAULT_RESPONSE

        app = create_rebar_app(rebar)

        resp = app.test_client().get(path="/me", headers={"x-name": "hello"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {"user_name": "hello"})

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
        rebar.create_handler_registry(spec_path=None, swagger_ui_path=None)
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

    @parametrize(
        "foo_cls, foo_list_cls, headers_cls",
        [
            (FooSchema, FooListSchema, HeadersSchema),
            (FooModel, FooListModel, HeadersModel),
        ],
    )
    def test_bare_class_schemas_handled(self, foo_cls, foo_list_cls, headers_cls):
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        expected_headers = {"x-name": "Header Name"}

        def get_foo(*args, **kwargs):
            return expected_foo

        def post_foo(*args, **kwargs):
            return expected_foo

        register_endpoint(
            registry=registry,
            method="GET",
            path="/my_get_endpoint",
            headers_schema=headers_cls,
            response_body_schema={200: foo_cls},
            query_string_schema=foo_list_cls,
            func=get_foo,
        )

        register_endpoint(
            registry=registry,
            method="POST",
            path="/my_post_endpoint",
            request_body_schema=foo_list_cls,
            response_body_schema=foo_cls,
            func=post_foo,
        )

        expected_foo = FooSchema().load({"uid": "some_uid", "name": "Namey McNamerton"})

        app = create_rebar_app(rebar)
        # violate headers schema:
        resp = app.test_client().get(path="/my_get_endpoint?name=QuerystringName")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json["message"], messages.header_validation_failed.message
        )

        # violate querystring schema:
        resp = app.test_client().get(path="/my_get_endpoint", headers=expected_headers)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json["message"], messages.query_string_validation_failed.message
        )
        # valid request:
        resp = app.test_client().get(
            path="/my_get_endpoint?name=QuerystringName", headers=expected_headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, expected_foo)

        resp = app.test_client().post(
            path="/my_post_endpoint",
            data='{"wrong": "Posted Name"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json["message"], messages.body_validation_failed.message)

        resp = app.test_client().post(
            path="/my_post_endpoint",
            data='{"name": "Posted Name"}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # ensure Swagger generation doesn't break (Issue #115)
        from flask_rebar import SwaggerV2Generator, SwaggerV3Generator

        swagger = SwaggerV2Generator().generate(registry)
        self.assertIsNotNone(swagger)  # really only care that it didn't barf
        swagger = SwaggerV3Generator().generate(registry)
        self.assertIsNotNone(swagger)
