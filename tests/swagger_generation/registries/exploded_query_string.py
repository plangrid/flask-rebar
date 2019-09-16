import marshmallow

from flask_rebar import Rebar
from flask_rebar import RequestSchema
from flask_rebar.validation import QueryParamList
from flask_rebar.swagger_generation import SwaggerV2Generator, SwaggerV3Generator

rebar = Rebar()
registry = rebar.create_handler_registry()

swagger_v2_generator = SwaggerV2Generator()
swagger_v3_generator = SwaggerV3Generator()


class ExplodedQueryStringSchema(RequestSchema):
    foos = QueryParamList(marshmallow.fields.String(), required=True)


@registry.handles(
    rule="/foos", method="GET", query_string_schema=ExplodedQueryStringSchema()
)
def get_foos():
    pass


EXPECTED_SWAGGER_V2 = {
    "swagger": "2.0",
    "host": "swag.com",
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "schemes": [],
    "securityDefinitions": {},
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "definitions": {
        "Error": {
            "type": "object",
            "title": "Error",
            "properties": {"message": {"type": "string"}, "errors": {"type": "object"}},
            "required": ["message"],
        }
    },
    "paths": {
        "/foos": {
            "get": {
                "operationId": "get_foos",
                "responses": {
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    }
                },
                "parameters": [
                    {
                        "name": "foos",
                        "in": "query",
                        "required": True,
                        "collectionFormat": "multi",
                        "type": "array",
                        "items": {"type": "string"},
                    }
                ],
            }
        }
    },
}

EXPECTED_SWAGGER_V3 = {
    "openapi": "3.0.2",
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "title": "Error",
                "properties": {
                    "message": {"type": "string"},
                    "errors": {"type": "object"},
                },
                "required": ["message"],
            }
        }
    },
    "paths": {
        "/foos": {
            "get": {
                "operationId": "get_foos",
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
                "parameters": [
                    {
                        "name": "foos",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "array", "items": {"type": "string"}},
                        "explode": True,
                    }
                ],
            }
        }
    },
}
