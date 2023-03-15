"""
    Test Swagger Generation
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests for converting a handler registry to a Swagger specification.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json
import pytest
from flask_rebar.testing import validate_swagger
from flask_rebar.testing.swagger_jsonschema import (
    SWAGGER_V2_JSONSCHEMA,
    SWAGGER_V3_JSONSCHEMA,
)

from tests.swagger_generation.registries import hidden_api


def _assert_dicts_equal(a, b):
    result = json.dumps(a, indent=2, sort_keys=True)
    expected = json.dumps(b, indent=2, sort_keys=True)

    assert result == expected


@pytest.mark.parametrize(
    "registry, swagger_generator, expected_swagger",
    [
        (
            hidden_api.registry,
            hidden_api.swagger_v2_generator,
            hidden_api.EXPECTED_SWAGGER_V2,
        ),
        (
            hidden_api.registry,
            hidden_api.normal_swagger_v3_generator,
            hidden_api.SWAGGER_V3_WITHOUT_HIDDEN,
        ),
        (
            hidden_api.registry,
            hidden_api.swagger_v3_generator_with_hidden,
            hidden_api.SWAGGER_V3_WITH_HIDDEN,
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
        raise ValueError("Unknown swagger_version: {}".format(open_api_version))

    validate_swagger(expected_swagger, schema=swagger_jsonschema)

    swagger = swagger_generator.generate(registry)

    result = json.dumps(swagger, indent=2, sort_keys=True)
    expected = json.dumps(expected_swagger, indent=2, sort_keys=True)

    assert result == expected
