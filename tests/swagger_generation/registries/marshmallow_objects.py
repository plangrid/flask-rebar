import marshmallow as m
import marshmallow_objects as mo

from flask_rebar import Rebar
from flask_rebar import HeaderApiKeyAuthenticator
from flask_rebar import compat
from flask_rebar.utils.marshmallow_objects_helpers import NestedTitledModel
from flask_rebar.swagger_generation import SwaggerV2Generator, SwaggerV3Generator

rebar = Rebar()
registry = rebar.create_handler_registry()

swagger_v2_generator = SwaggerV2Generator()
swagger_v3_generator = SwaggerV3Generator()

authenticator = HeaderApiKeyAuthenticator(header="x-auth")
default_authenticator = HeaderApiKeyAuthenticator(header="x-another", name="default")


class HeaderModel(mo.Model):
    user_id = compat.set_data_key(field=m.fields.String(required=True), key="X-UserId")


class FooModel(mo.Model):
    __swagger_title__ = "Foo"

    uid = mo.fields.String()
    name = mo.fields.String()


class NestedFoosModel(mo.Model):
    data = NestedTitledModel(FooModel, "Foo", many=True)


class FooUpdateModel(mo.Model):
    __swagger_title = "FooUpdate"

    name = mo.fields.String()


class NameAndOtherModel(mo.Model):
    name = mo.fields.String()
    other = mo.fields.String()


@registry.handles(
    rule="/foos/<uuid_string:foo_uid>",
    method="GET",
    response_body_schema={200: FooModel},
    headers_schema=HeaderModel,
)
def get_foo(foo_uid):
    """helpful description"""
    pass


@registry.handles(
    rule="/foos/<foo_uid>",
    method="PATCH",
    response_body_schema={200: FooModel},
    request_body_schema=FooUpdateModel,
    authenticator=authenticator,
)
def update_foo(foo_uid):
    pass


@registry.handles(
    rule="/foos",
    method="GET",
    response_body_schema={200: NestedFoosModel},
    query_string_schema=NameAndOtherModel,
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
                        "name": "FooUpdateModelSchema",
                        "in": "body",
                        "required": True,
                        "schema": {"$ref": "#/definitions/FooUpdateModelSchema"},
                    }
                ],
                "security": [{"sharedSecret": []}],
            },
        },
        "/foos": {
            "get": {
                "operationId": "nested_foos",
                "responses": {
                    "200": {
                        "description": "NestedFoosModelSchema",
                        "schema": {"$ref": "#/definitions/NestedFoosModelSchema"},
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
            "additionalProperties": False,
            "type": "object",
            "title": "Foo",
            "properties": {"uid": {"type": "string"}, "name": {"type": "string"}},
        },
        "FooUpdateModelSchema": {
            "additionalProperties": False,
            "type": "object",
            "title": "FooUpdateModelSchema",
            "properties": {"name": {"type": "string"}},
        },
        "NestedFoosModelSchema": {
            "additionalProperties": False,
            "type": "object",
            "title": "NestedFoosModelSchema",
            "properties": {
                "data": {
                    "additionalProperties": False,
                    "type": "array",
                    "items": {"$ref": "#/definitions/Foo"},
                }
            },
        },
        "Error": {
            "additionalProperties": False,
            "type": "object",
            "title": "Error",
            "properties": {"message": {"type": "string"}, "errors": {"type": "object"}},
            "required": ["message"],
        },
    },
}


EXPECTED_SWAGGER_V3 = expected_swagger = {
    "openapi": "3.1.0",
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "security": [{"default": []}],
    "components": {
        "schemas": {
            "Foo": {
                "additionalProperties": False,
                "type": "object",
                "title": "Foo",
                "properties": {"uid": {"type": "string"}, "name": {"type": "string"}},
            },
            "FooUpdateModelSchema": {
                "additionalProperties": False,
                "type": "object",
                "title": "FooUpdateModelSchema",
                "properties": {"name": {"type": "string"}},
            },
            "NestedFoosModelSchema": {
                "additionalProperties": False,
                "type": "object",
                "title": "NestedFoosModelSchema",
                "properties": {
                    "data": {
                        "additionalProperties": False,
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Foo"},
                    }
                },
            },
            "Error": {
                "additionalProperties": False,
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
                            "schema": {
                                "$ref": "#/components/schemas/FooUpdateModelSchema"
                            }
                        }
                    },
                    "required": True,
                },
                "security": [{"sharedSecret": []}],
            },
        },
        "/foos": {
            "get": {
                "operationId": "nested_foos",
                "responses": {
                    "200": {
                        "description": "NestedFoosModelSchema",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/NestedFoosModelSchema"
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
