import jsonschema
import yaml

from flask_rebar.testing.swagger_jsonschema import SWAGGER_V2_JSONSCHEMA


def validate_swagger(swagger, schema_major=2):
    """
    Validates that a dictionary is a valid Swagger spec.

    :param dict swagger: The swagger spec
    :param int schema_major: The Swagger/OpenAPI spec version to use to validate the swagger spec
    :raises: jsonschema.ValidationError
    """
    if schema_major == 2:
        schema = SWAGGER_V2_JSONSCHEMA
    elif schema_major == 3:
        with open('flask_rebar/testing/openapi_3.0_schema.yaml', 'r') as f:
            schema = yaml.load(f)
    else:
        raise NotImplementedError()

    jsonschema.validate(
        instance=swagger,
        schema=schema
    )
