import jsonschema

from flask_rebar.testing.swagger_jsonschema import SWAGGER_V2_JSONSCHEMA


def validate_swagger(swagger, schema=SWAGGER_V2_JSONSCHEMA):
    """
    Validates that a dictionary is a valid Swagger spec.

    :param dict swagger: The swagger spec
    :param dict schema: The JSON Schema to use to validate the swagger spec
    :raises: jsonschema.ValidationError
    """
    jsonschema.validate(instance=swagger, schema=schema)
