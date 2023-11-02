"""
    Test Swagger Generation
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests for converting a handler registry to a Swagger specification.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json

import marshmallow as m
import pytest

from flask_rebar.rebar import Rebar
from flask_rebar.swagger_generation import ExternalDocumentation
from flask_rebar.swagger_generation import SwaggerV2Generator
from flask_rebar.swagger_generation import SwaggerV3Generator
from flask_rebar.swagger_generation import Server
from flask_rebar.swagger_generation import ServerVariable
from flask_rebar.swagger_generation import Tag
from flask_rebar.testing import validate_swagger
from flask_rebar.testing.swagger_jsonschema import (
    SWAGGER_V2_JSONSCHEMA,
    SWAGGER_V3_JSONSCHEMA,
)

from tests.swagger_generation.registries import (
    legacy,
    exploded_query_string,
    marshmallow_objects,
    multiple_authenticators,
)


def _assert_dicts_equal(a, b):
    result = json.dumps(a, indent=2, sort_keys=True)
    expected = json.dumps(b, indent=2, sort_keys=True)

    assert result == expected


def test_swagger_v2_generator_non_registry_parameters():
    host = "localhost"
    schemes = ["http"]
    consumes = ["application/json"]
    produces = ["application/json"]
    title = "Test API"
    version = "2.1.0"
    description = "Foo Bar Baz"

    class Error(m.Schema):
        message = m.fields.String()
        details = m.fields.Dict()

    generator = SwaggerV2Generator(
        host=host,
        schemes=schemes,
        consumes=consumes,
        produces=produces,
        title=title,
        version=version,
        description=description,
        default_response_schema=Error(),
        tags=[
            Tag(
                name="bar",
                description="baz",
                external_docs=ExternalDocumentation(
                    url="http://bardocs.com", description="qux"
                ),
            )
        ],
    )

    rebar = Rebar()
    registry = rebar.create_handler_registry()

    swagger = generator.generate(registry)

    expected_swagger = {
        "swagger": "2.0",
        "host": host,
        "info": {"title": title, "version": version, "description": description},
        "schemes": schemes,
        "consumes": consumes,
        "produces": produces,
        "securityDefinitions": {},
        "tags": [
            {
                "name": "bar",
                "description": "baz",
                "externalDocs": {"url": "http://bardocs.com", "description": "qux"},
            }
        ],
        "paths": {},
        "definitions": {
            "Error": {
                "additionalProperties": False,
                "type": "object",
                "title": "Error",
                "properties": {
                    "message": {"type": "string"},
                    "details": {"type": "object"},
                },
            }
        },
    }

    validate_swagger(expected_swagger)
    _assert_dicts_equal(swagger, expected_swagger)


def test_swagger_v3_generator_non_registry_parameters():
    title = "Test API"
    version = "3.1.0"
    description = "testing testing 123"

    class Error(m.Schema):
        message = m.fields.String()
        details = m.fields.Dict()

    generator = SwaggerV3Generator(
        version=version,
        title=title,
        description=description,
        default_response_schema=Error(),
        tags=[
            Tag(
                name="bar",
                description="baz",
                external_docs=ExternalDocumentation(
                    url="http://bardocs.com", description="qux"
                ),
            )
        ],
        servers=[
            Server(
                url="https://{username}.gigantic-server.com:{port}/{basePath}",
                description="The production API server",
                variables={
                    "username": ServerVariable(
                        default="demo",
                        description="this value is assigned by the service provider: `gigantic-server.com`",
                    ),
                    "port": ServerVariable(default="8443", enum=["8443", "443"]),
                    "basePath": ServerVariable(default="v2"),
                },
            )
        ],
    )

    rebar = Rebar()
    registry = rebar.create_handler_registry()

    swagger = generator.generate(registry)

    expected_swagger = {
        "openapi": "3.1.0",
        "info": {"title": title, "version": version, "description": description},
        "tags": [
            {
                "name": "bar",
                "description": "baz",
                "externalDocs": {"url": "http://bardocs.com", "description": "qux"},
            }
        ],
        "servers": [
            {
                "url": "https://{username}.gigantic-server.com:{port}/{basePath}",
                "description": "The production API server",
                "variables": {
                    "username": {
                        "default": "demo",
                        "description": "this value is assigned by the service provider: `gigantic-server.com`",
                    },
                    "port": {"enum": ["8443", "443"], "default": "8443"},
                    "basePath": {"default": "v2"},
                },
            }
        ],
        "paths": {},
        "components": {
            "schemas": {
                "Error": {
                    "additionalProperties": False,
                    "type": "object",
                    "title": "Error",
                    "properties": {
                        "message": {"type": "string"},
                        "details": {"type": "object"},
                    },
                }
            }
        },
    }
    validate_swagger(expected_swagger, SWAGGER_V3_JSONSCHEMA)
    _assert_dicts_equal(swagger, expected_swagger)


@pytest.mark.parametrize("generator", [SwaggerV3Generator()])
def test_swagger_v3_generator_response_content_type(generator):
    rebar = Rebar()
    registry = rebar.create_handler_registry()

    class PDF(m.fields.String):
        __content_type__ = "application/pdf"

    @registry.handles(rule="/foos/pdf", method="GET", response_body_schema={201: PDF})
    def get_foo(foo_uid):
        pass

    expected_swagger = {
        "components": {
            "schemas": {
                "Error": {
                    "properties": {
                        "errors": {"type": "object"},
                        "message": {"type": "string"},
                    },
                    "required": ["message"],
                    "title": "Error",
                    "type": "object",
                }
            }
        },
        "info": {"description": "", "title": "My API", "version": "1.0.0"},
        "openapi": "3.0.2",
        "paths": {
            "/foos/pdf": {
                "get": {
                    "operationId": "get_foo",
                    "responses": {
                        "201": {
                            "content": {
                                "application/pdf": {"schema": {"type": "string"}}
                            },
                            "description": "PDF",
                        },
                        "default": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Error"}
                                }
                            },
                            "description": "Error",
                        },
                    },
                }
            }
        },
    }
    swagger = generator.generate(registry)
    validate_swagger(expected_swagger, SWAGGER_V3_JSONSCHEMA)
    _assert_dicts_equal(swagger, expected_swagger)


@pytest.mark.parametrize("generator", [SwaggerV2Generator(), SwaggerV3Generator()])
def test_path_parameter_types_must_be_the_same_for_same_path(generator):
    rebar = Rebar()
    registry = rebar.create_handler_registry()

    @registry.handles(rule="/foos/<string:foo_uid>", method="GET")
    def get_foo(foo_uid):
        pass

    @registry.handles(rule="/foos/<int:foo_uid>", method="PATCH")
    def update_foo(foo_uid):
        pass

    with pytest.raises(ValueError):
        generator.generate(registry)


@pytest.mark.parametrize(
    "registry, swagger_generator, expected_swagger",
    [
        (legacy.registry, legacy.swagger_v2_generator, legacy.EXPECTED_SWAGGER_V2),
        (legacy.registry, legacy.swagger_v3_generator, legacy.EXPECTED_SWAGGER_V3),
        (
            exploded_query_string.registry,
            exploded_query_string.swagger_v2_generator,
            exploded_query_string.EXPECTED_SWAGGER_V2,
        ),
        (
            exploded_query_string.registry,
            exploded_query_string.swagger_v3_generator,
            exploded_query_string.EXPECTED_SWAGGER_V3,
        ),
        (
            multiple_authenticators.registry,
            multiple_authenticators.swagger_v2_generator,
            multiple_authenticators.EXPECTED_SWAGGER_V2,
        ),
        (
            multiple_authenticators.registry,
            multiple_authenticators.swagger_v3_generator,
            multiple_authenticators.EXPECTED_SWAGGER_V3,
        ),
        (
            marshmallow_objects.registry,
            marshmallow_objects.swagger_v2_generator,
            marshmallow_objects.EXPECTED_SWAGGER_V2,
        ),
        (
            marshmallow_objects.registry,
            marshmallow_objects.swagger_v3_generator,
            marshmallow_objects.EXPECTED_SWAGGER_V3,
        ),
    ],
)
def test_swagger_generators(registry, swagger_generator, expected_swagger):
    open_api_version = swagger_generator.get_open_api_version()
    if open_api_version == "2.0":
        swagger_jsonschema = SWAGGER_V2_JSONSCHEMA
    elif open_api_version == "3.1.0":
        swagger_jsonschema = SWAGGER_V3_JSONSCHEMA
    else:
        raise ValueError(f"Unknown swagger_version: {open_api_version}")

    validate_swagger(expected_swagger, schema=swagger_jsonschema)

    swagger = swagger_generator.generate(registry)

    result = json.dumps(swagger, indent=2, sort_keys=True)
    expected = json.dumps(expected_swagger, indent=2, sort_keys=True)

    assert result == expected
