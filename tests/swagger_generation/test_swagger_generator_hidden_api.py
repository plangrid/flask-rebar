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
    hidden_api_authenticator,
    include_hidden_api_authenticator,
)


def _assert_dicts_equal(a, b):
    result = json.dumps(a, indent=2, sort_keys=True)
    expected = json.dumps(b, indent=2, sort_keys=True)

    assert result == expected


def test_swagger_v3_generator_non_registry_parameters():
    title = "Test API"
    version = "3.0.0"
    description = "testing testing 123"

    class Error(m.Schema):
        message = m.fields.String()
        details = m.fields.Dict()

    generator = SwaggerV3Generator(
        version="3.0.0",
        include_hidden=True,
        title="Test API",
        description="testing testing 123",
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
                        description="this value is assigned by the service provider, in this example `gigantic-server.com`",
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
        "openapi": "3.0.2",
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
                        "description": "this value is assigned by the service provider, in this example `gigantic-server.com`",
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


@pytest.mark.parametrize(
    "registry, swagger_generator, expected_swagger",
    [
        (
            hidden_api_authenticator.registry,
            hidden_api_authenticator.swagger_v2_generator,
            hidden_api_authenticator.EXPECTED_SWAGGER_V2,
        ),
        (
            hidden_api_authenticator.registry,
            hidden_api_authenticator.swagger_v3_generator,
            hidden_api_authenticator.EXPECTED_SWAGGER_V3,
        ),
        (
            include_hidden_api_authenticator.registry,
            include_hidden_api_authenticator.swagger_v2_generator,
            include_hidden_api_authenticator.EXPECTED_SWAGGER_V2,
        ),
        (
            include_hidden_api_authenticator.registry,
            include_hidden_api_authenticator.swagger_v3_generator,
            include_hidden_api_authenticator.EXPECTED_SWAGGER_V3,
        ),
    ],
)
def test_swagger_generators(registry, swagger_generator, expected_swagger):
    open_api_version = swagger_generator.get_open_api_version()
    if open_api_version == "2.0":
        swagger_jsonschema = SWAGGER_V2_JSONSCHEMA
    elif open_api_version == "3.0.2":
        swagger_jsonschema = SWAGGER_V3_JSONSCHEMA
    else:
        raise ValueError("Unknown swagger_version: {}".format(open_api_version))

    validate_swagger(expected_swagger, schema=swagger_jsonschema)

    swagger = swagger_generator.generate(registry)

    result = json.dumps(swagger, indent=2, sort_keys=True)
    expected = json.dumps(expected_swagger, indent=2, sort_keys=True)

    assert result == expected
