import marshmallow as m

from flask_rebar import Rebar
from flask_rebar import HeaderApiKeyAuthenticator
from flask_rebar import compat
from flask_rebar.swagger_generation import SwaggerV2Generator, SwaggerV3Generator

rebar = Rebar()
registry = rebar.create_handler_registry()

swagger_v2_generator = SwaggerV2Generator()
swagger_v3_generator = SwaggerV3Generator()

authenticator = HeaderApiKeyAuthenticator(header="x-auth")
default_authenticator = HeaderApiKeyAuthenticator(header="x-another", name="default")


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
    the summary

    helpful description
    """
    pass


@registry.handles(
    rule="/foos/<foo_uid>",
    method="PATCH",
    marshal_schema={200: FooSchema()},
    request_body_schema=FooUpdateSchema(),
    authenticator=authenticator,
)
def update_foo(foo_uid):
    pass


# Test using Schema(many=True) without using a nested Field.
# https://github.com/plangrid/flask-rebar/issues/41
@registry.handles(
    rule="/foo_list",
    method="GET",
    marshal_schema={200: FooSchema(many=True)},
    authenticator=None,  # Override the default!
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


registry.set_default_authenticator(default_authenticator)


EXPECTED_SWAGGER_V2 = {
    "swagger": "2.0",
    "host": "localhost",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "schemes": [],
    "securityDefinitions": {
        "sharedSecret": {"type": "apiKey", "in": "header", "name": "x-auth"},
        "default": {"type": "apiKey", "in": "header", "name": "x-another"},
    },
    "security": [{"default": []}],
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "paths": {
        "/foos/{foo_uid}": {
            "parameters": [
                {"name": "foo_uid", "in": "path", "required": True, "type": "string"}
            ],
            "get": {
                "operationId": "get_foo",
                "description": "helpful description",
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
                "summary": "the summary",
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
                "security": [{"sharedSecret": []}],
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
                "security": [],
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
    "security": [{"default": []}],
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
            "sharedSecret": {"type": "apiKey", "in": "header", "name": "x-auth"},
            "default": {"type": "apiKey", "in": "header", "name": "x-another"},
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
                "description": "helpful description",
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
                "summary": "the summary",
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
                "security": [{"sharedSecret": []}],
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
                "security": [],
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
