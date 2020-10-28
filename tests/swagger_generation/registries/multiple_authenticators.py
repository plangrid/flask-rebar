import marshmallow as m

from flask_rebar import Rebar, HeaderApiKeyAuthenticator, compat
from flask_rebar.authenticators import Authenticator, USE_DEFAULT
from flask_rebar.swagger_generation import SwaggerV2Generator, SwaggerV3Generator
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    AuthenticatorConverterRegistry,
    AuthenticatorConverter,
    HeaderApiKeyConverter,
)

rebar = Rebar()
registry = rebar.create_handler_registry()

authenticator_converter_registry = AuthenticatorConverterRegistry()

swagger_v2_generator = SwaggerV2Generator(
    authenticator_converter_registry=authenticator_converter_registry
)
swagger_v3_generator = SwaggerV3Generator(
    authenticator_converter_registry=authenticator_converter_registry
)


# If we ever add a HTTP 'Authorization' authenticator then use that.
class FakeHTTPAuthorizationAuthenticator(Authenticator):
    name = "basicAuth"
    schema = "basic"

    def authenticate(self):
        return


class HTTPAuthorizationAuthenticatorConverter(AuthenticatorConverter):

    AUTHENTICATOR_TYPE = FakeHTTPAuthorizationAuthenticator

    def get_security_schemes(self, instance, context):
        if context.openapi_version == 2:
            return {instance.name: {"type": "basic"}}
        elif context.openapi_version == 3:
            return {instance.name: {"type": "http", "scheme": "basic"}}
        else:
            raise ValueError("Unsupported OpenAPI Version")

    def get_security_requirements(self, instance, context):
        return [{instance.name: []}]


# If we ever add an OAuth2 authenticator then use that.
class FakeOAuth2Authenticator(Authenticator):
    name = "oauth2"

    def __init__(self, required_scopes=None):
        self.required_scopes = required_scopes or []
        self.supported_flows = {
            "implicit": {
                "authorizationUrl": "https://example.com/authorize",
                "scopes": {
                    "write:stuff": "Modify your stuff",
                    "read:stuff": "Read your stuff",
                },
            }
        }

    def authenticate(self):
        return


class OAuth2AuthenticatorConverter(AuthenticatorConverter):

    AUTHENTICATOR_TYPE = FakeOAuth2Authenticator

    def get_security_schemes(self, instance, context):
        if context.openapi_version == 2:
            return {
                instance.name
                + "_"
                + flow: {
                    key: value
                    for key, value in {
                        "type": "oauth2",
                        "flow": flow,
                        "authorizationUrl": config.get("authorizationUrl", None),
                        "tokenUrl": config.get("tokenUrl", None),
                        "refreshUrl": config.get("refreshUrl", None),
                        "scopes": config.get("scopes", []),
                    }.items()
                    if value is not None
                }
                for flow, config in instance.supported_flows.items()
            }
        elif context.openapi_version == 3:
            return {
                instance.name: {"type": "oauth2", "flows": instance.supported_flows}
            }
        else:
            raise ValueError("Unsupported OpenAPI Version")

    def get_security_requirements(self, instance, context):
        if context.openapi_version == 2:
            return [
                {
                    instance.name + "_" + flow: instance.required_scopes
                    for flow in instance.supported_flows
                }
            ]
        elif context.openapi_version == 3:
            return [{instance.name: instance.required_scopes}]
        else:
            raise ValueError("Unsupported OpenAPI Version")


class FakeComplexAuthenticator(Authenticator):
    name = "complexAuth"

    def __init__(self, header, url, required_scopes=None):
        self.required_scopes = required_scopes or []
        self.url = url
        self.api_key = header

    def authenticate(self):
        return


class ComplexAuthenticatorConverter(AuthenticatorConverter):

    AUTHENTICATOR_TYPE = FakeComplexAuthenticator

    def get_security_schemes(self, instance, context):
        if context.openapi_version == 2:
            return {
                "openIDConnect": {
                    "type": "oauth2",  # Not supported so use this for tests.
                    "flow": "implicit",
                    "authorizationUrl": instance.url,
                },
                "application_key": {
                    "type": "apiKey",
                    "in": "header",
                    "name": instance.api_key,
                },
            }
        elif context.openapi_version == 3:
            return {
                "openIDConnect": {
                    "type": "openIdConnect",
                    "openIdConnectUrl": instance.url,
                },
                "application_key": {
                    "type": "apiKey",
                    "in": "header",
                    "name": instance.api_key,
                },
            }
        else:
            raise ValueError("Unsupported OpenAPI Version")

    def get_security_requirements(self, instance, context):
        return [{"openIDConnect": instance.required_scopes, "application_key": []}]


authenticator_converter_registry.register_types(
    [
        HeaderApiKeyConverter(),
        HTTPAuthorizationAuthenticatorConverter(),
        OAuth2AuthenticatorConverter(),
        ComplexAuthenticatorConverter(),
    ]
)


default_authenticator = FakeOAuth2Authenticator(required_scopes=["read:stuff"])
alternative_default_authenticator = HeaderApiKeyAuthenticator(header="x-api-key")

authenticator = FakeHTTPAuthorizationAuthenticator()
alternative_authenticator = FakeComplexAuthenticator(
    header="x-app-id",
    url="https://exmaple.com/openconnect",
    required_scopes=["write:junk", "write:stuff"],
)

customer_authenticator_converter_registry = [
    HTTPAuthorizationAuthenticatorConverter(),
    OAuth2AuthenticatorConverter(),
    ComplexAuthenticatorConverter(),
]


class HeaderSchema(m.Schema):
    user_id = compat.set_data_key(field=m.fields.String(required=True), key="X-UserId")


class FooSchema(m.Schema):
    __swagger_title__ = "Foo"

    uid = m.fields.String()
    name = m.fields.String()


class NestedFoosSchema(m.Schema):
    data = m.fields.Nested(FooSchema, many=True)


class FooUpdateSchema(m.Schema):
    __swagger_title = "FooUpdate"

    name = m.fields.String()


class NameAndOtherSchema(m.Schema):
    name = m.fields.String()
    other = m.fields.String()


@registry.handles(
    rule="/foos/<uuid_string:foo_uid>",
    method="GET",
    marshal_schema={200: FooSchema()},
    headers_schema=HeaderSchema(),
)
def get_foo(foo_uid):
    """
    a summary

    P1 L1
    P1 L2

    P2 L1
    P2 L2
    """
    pass


@registry.handles(
    rule="/foos/<foo_uid>",
    method="PATCH",
    marshal_schema={200: FooSchema()},
    request_body_schema=FooUpdateSchema(),
    authenticators=authenticator,
)
def update_foo(foo_uid):
    pass


# Test using Schema(many=True) without using a nested Field.
# https://github.com/plangrid/flask-rebar/issues/41
@registry.handles(
    rule="/foo_list",
    method="GET",
    marshal_schema={200: FooSchema(many=True)},
    authenticators=[USE_DEFAULT, alternative_authenticator],  # Extend the default!
)
def list_foos():
    pass


@registry.handles(
    rule="/foos",
    method="GET",
    marshal_schema={200: NestedFoosSchema()},
    query_string_schema=NameAndOtherSchema(),
    authenticator=None,  # Override the default!
)
def nested_foos():
    pass


@registry.handles(rule="/tagged_foos", tags=["bar", "baz"])
def tagged_foos():
    pass


registry.set_default_authenticators(
    [default_authenticator, alternative_default_authenticator]
)


EXPECTED_SWAGGER_V2 = {
    "swagger": "2.0",
    "host": "localhost",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "schemes": [],
    "securityDefinitions": {
        "oauth2_implicit": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": "https://example.com/authorize",
            "scopes": {
                "write:stuff": "Modify your stuff",
                "read:stuff": "Read your stuff",
            },
        },
        "sharedSecret": {"type": "apiKey", "in": "header", "name": "x-api-key"},
        "basicAuth": {"type": "basic"},
        "openIDConnect": {
            "type": "oauth2",
            "flow": "implicit",
            "authorizationUrl": "https://exmaple.com/openconnect",
        },
        "application_key": {"type": "apiKey", "in": "header", "name": "x-app-id"},
    },
    "security": [{"oauth2_implicit": ["read:stuff"]}, {"sharedSecret": []}],
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "paths": {
        "/foos/{foo_uid}": {
            "parameters": [
                {"name": "foo_uid", "in": "path", "required": True, "type": "string"}
            ],
            "get": {
                "operationId": "get_foo",
                "description": "P1 L1\nP1 L2\n\nP2 L1\nP2 L2",
                "responses": {
                    "200": {
                        "description": "Foo",
                        "schema": {"$ref": "#/definitions/Foo"},
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
                "parameters": [
                    {
                        "name": "X-UserId",
                        "in": "header",
                        "required": True,
                        "type": "string",
                    }
                ],
                "summary": "a summary",
            },
            "patch": {
                "operationId": "update_foo",
                "responses": {
                    "200": {
                        "description": "Foo",
                        "schema": {"$ref": "#/definitions/Foo"},
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
                "parameters": [
                    {
                        "name": "FooUpdateSchema",
                        "in": "body",
                        "required": True,
                        "schema": {"$ref": "#/definitions/FooUpdateSchema"},
                    }
                ],
                "security": [{"basicAuth": []}],
            },
        },
        "/foo_list": {
            "get": {
                "operationId": "list_foos",
                "responses": {
                    "200": {
                        "description": "Foo",
                        "schema": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/Foo"},
                        },
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
                "security": [
                    {"oauth2_implicit": ["read:stuff"]},
                    {"sharedSecret": []},
                    {
                        "openIDConnect": ["write:junk", "write:stuff"],
                        "application_key": [],
                    },
                ],
            }
        },
        "/foos": {
            "get": {
                "operationId": "nested_foos",
                "responses": {
                    "200": {
                        "description": "NestedFoosSchema",
                        "schema": {"$ref": "#/definitions/NestedFoosSchema"},
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
                "parameters": [
                    {
                        "name": "name",
                        "in": "query",
                        "required": False,
                        "type": "string",
                    },
                    {
                        "name": "other",
                        "in": "query",
                        "required": False,
                        "type": "string",
                    },
                ],
                "security": [],
            }
        },
        "/tagged_foos": {
            "get": {
                "tags": ["bar", "baz"],
                "operationId": "tagged_foos",
                "responses": {
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    }
                },
            }
        },
    },
    "definitions": {
        "Foo": {
            "type": "object",
            "title": "Foo",
            "properties": {"uid": {"type": "string"}, "name": {"type": "string"}},
        },
        "FooUpdateSchema": {
            "type": "object",
            "title": "FooUpdateSchema",
            "properties": {"name": {"type": "string"}},
        },
        "NestedFoosSchema": {
            "type": "object",
            "title": "NestedFoosSchema",
            "properties": {
                "data": {"type": "array", "items": {"$ref": "#/definitions/Foo"}}
            },
        },
        "Error": {
            "type": "object",
            "title": "Error",
            "properties": {"message": {"type": "string"}, "errors": {"type": "object"}},
            "required": ["message"],
        },
    },
}


EXPECTED_SWAGGER_V3 = expected_swagger = {
    "openapi": "3.0.2",
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "security": [{"oauth2": ["read:stuff"]}, {"sharedSecret": []}],
    "components": {
        "schemas": {
            "Foo": {
                "type": "object",
                "title": "Foo",
                "properties": {"uid": {"type": "string"}, "name": {"type": "string"}},
            },
            "FooUpdateSchema": {
                "type": "object",
                "title": "FooUpdateSchema",
                "properties": {"name": {"type": "string"}},
            },
            "NestedFoosSchema": {
                "type": "object",
                "title": "NestedFoosSchema",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Foo"},
                    }
                },
            },
            "Error": {
                "type": "object",
                "title": "Error",
                "properties": {
                    "message": {"type": "string"},
                    "errors": {"type": "object"},
                },
                "required": ["message"],
            },
        },
        "securitySchemes": {
            "oauth2": {
                "type": "oauth2",
                "flows": {
                    "implicit": {
                        "authorizationUrl": "https://example.com/authorize",
                        "scopes": {
                            "write:stuff": "Modify your stuff",
                            "read:stuff": "Read your stuff",
                        },
                    }
                },
            },
            "sharedSecret": {"type": "apiKey", "in": "header", "name": "x-api-key"},
            "basicAuth": {"type": "http", "scheme": "basic"},
            "openIDConnect": {
                "type": "openIdConnect",
                "openIdConnectUrl": "https://exmaple.com/openconnect",
            },
            "application_key": {"type": "apiKey", "in": "header", "name": "x-app-id"},
        },
    },
    "paths": {
        "/foos/{foo_uid}": {
            "parameters": [
                {
                    "name": "foo_uid",
                    "in": "path",
                    "required": True,
                    "style": "simple",
                    "schema": {"type": "string"},
                }
            ],
            "get": {
                "operationId": "get_foo",
                "description": "P1 L1\nP1 L2\n\nP2 L1\nP2 L2",
                "responses": {
                    "200": {
                        "description": "Foo",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Foo"}
                            }
                        },
                    },
                    "default": {
                        "description": "Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
                "parameters": [
                    {
                        "name": "X-UserId",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "summary": "a summary",
            },
            "patch": {
                "operationId": "update_foo",
                "responses": {
                    "200": {
                        "description": "Foo",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Foo"}
                            }
                        },
                    },
                    "default": {
                        "description": "Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/FooUpdateSchema"}
                        }
                    },
                    "required": True,
                },
                "security": [{"basicAuth": []}],
            },
        },
        "/foo_list": {
            "get": {
                "operationId": "list_foos",
                "responses": {
                    "200": {
                        "description": "Foo",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Foo"},
                                }
                            }
                        },
                    },
                    "default": {
                        "description": "Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
                "security": [
                    {"oauth2": ["read:stuff"]},
                    {"sharedSecret": []},
                    {
                        "openIDConnect": ["write:junk", "write:stuff"],
                        "application_key": [],
                    },
                ],
            }
        },
        "/foos": {
            "get": {
                "operationId": "nested_foos",
                "responses": {
                    "200": {
                        "description": "NestedFoosSchema",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/NestedFoosSchema"
                                }
                            }
                        },
                    },
                    "default": {
                        "description": "Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    },
                },
                "parameters": [
                    {
                        "name": "name",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                    {
                        "name": "other",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                    },
                ],
                "security": [],
            }
        },
        "/tagged_foos": {
            "get": {
                "tags": ["bar", "baz"],
                "operationId": "tagged_foos",
                "responses": {
                    "default": {
                        "description": "Error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        },
                    }
                },
            }
        },
    },
}
