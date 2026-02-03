"""
Test registry for DeepFriedMarshmallow schemas.

This module tests that DeepFriedMarshmallow's JitSchema works correctly
as a drop-in replacement for marshmallow.Schema when generating Swagger specs.
"""
from deepfriedmarshmallow import JitSchema
from marshmallow import fields

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


class ArtistSchema(JitSchema):
    """Artist schema using DeepFriedMarshmallow's JitSchema."""
    name = fields.Str()


class AlbumSchema(JitSchema):
    """Album schema using DeepFriedMarshmallow's JitSchema with nested schema."""
    title = fields.Str()
    release_date = fields.Date()
    artist = fields.Nested(ArtistSchema())


class AlbumUpdateSchema(JitSchema):
    """Schema for updating album - partial fields."""
    title = fields.Str()


class HeaderSchema(JitSchema):
    """Header schema for testing header parameters."""
    user_id = compat.set_data_key(field=fields.String(required=True), key="X-UserId")


class CompressedSheetText(JitSchema):
    """Schema with List field to test deepcopy recursion fix."""
    sheet = fields.UUID(required=True)
    text = fields.String(required=True)
    frame = fields.List(fields.Float(), required=True)


@registry.handles(
    rule="/albums/<uuid_string:album_uid>",
    method="GET",
    response_body_schema={200: AlbumSchema()},
    headers_schema=HeaderSchema(),
)
def get_album(album_uid):
    """Get an album by UID"""
    pass


@registry.handles(
    rule="/albums/<album_uid>",
    method="PATCH",
    response_body_schema={200: AlbumSchema()},
    request_body_schema=AlbumUpdateSchema(),
    authenticators=[authenticator],
)
def update_album(album_uid):
    """Update an album"""
    pass


@registry.handles(
    rule="/artists/<artist_uid>",
    method="GET",
    response_body_schema={200: ArtistSchema()},
    authenticators=None,  # Override the default!
)
def get_artist(artist_uid):
    """Get an artist by UID"""
    pass


@registry.handles(
    rule="/sheets",
    method="GET",
    response_body_schema={200: CompressedSheetText(many=True)},
)
def get_sheets():
    """Get multiple sheets - tests List field with many=True"""
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
        "/albums/{album_uid}": {
            "parameters": [
                {"name": "album_uid", "in": "path", "required": True, "type": "string"}
            ],
            "get": {
                "operationId": "get_album",
                "description": "Get an album by UID",
                "responses": {
                    "200": {
                        "description": "Album schema using DeepFriedMarshmallow's JitSchema with nested schema.",
                        "schema": {"$ref": "#/definitions/AlbumSchema"},
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
                "operationId": "update_album",
                "description": "Update an album",
                "responses": {
                    "200": {
                        "description": "Album schema using DeepFriedMarshmallow's JitSchema with nested schema.",
                        "schema": {"$ref": "#/definitions/AlbumSchema"},
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
                "parameters": [
                    {
                        "name": "AlbumUpdateSchema",
                        "in": "body",
                        "required": True,
                        "schema": {"$ref": "#/definitions/AlbumUpdateSchema"},
                    }
                ],
                "security": [{"sharedSecret": []}],
            },
        },
        "/artists/{artist_uid}": {
            "parameters": [
                {"name": "artist_uid", "in": "path", "required": True, "type": "string"}
            ],
            "get": {
                "operationId": "get_artist",
                "description": "Get an artist by UID",
                "responses": {
                    "200": {
                        "description": "Artist schema using DeepFriedMarshmallow's JitSchema.",
                        "schema": {"$ref": "#/definitions/ArtistSchema"},
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
                "security": [],
            },
        },
        "/sheets": {
            "get": {
                "operationId": "get_sheets",
                "description": "Get multiple sheets - tests List field with many=True",
                "responses": {
                    "200": {
                        "description": "Schema with List field to test deepcopy recursion fix.",
                        "schema": {
                            "type": "array",
                            "items": {"$ref": "#/definitions/CompressedSheetText"},
                        },
                    },
                    "default": {
                        "description": "Error",
                        "schema": {"$ref": "#/definitions/Error"},
                    },
                },
            },
        },
    },
    "definitions": {
        "AlbumSchema": {
            "type": "object",
            "title": "AlbumSchema",
            "additionalProperties": False,
            "description": "Album schema using DeepFriedMarshmallow's JitSchema with nested schema.",
            "properties": {
                "title": {"type": "string"},
                "release_date": {"type": "string", "format": "date"},
                "artist": {"$ref": "#/definitions/ArtistSchema"},
            },
        },
        "AlbumUpdateSchema": {
            "type": "object",
            "title": "AlbumUpdateSchema",
            "additionalProperties": False,
            "description": "Schema for updating album - partial fields.",
            "properties": {
                "title": {"type": "string"},
            },
        },
        "ArtistSchema": {
            "type": "object",
            "title": "ArtistSchema",
            "additionalProperties": False,
            "description": "Artist schema using DeepFriedMarshmallow's JitSchema.",
            "properties": {
                "name": {"type": "string"},
            },
        },
        "CompressedSheetText": {
            "type": "object",
            "title": "CompressedSheetText",
            "additionalProperties": False,
            "description": "Schema with List field to test deepcopy recursion fix.",
            "properties": {
                "sheet": {"type": "string", "format": "uuid"},
                "text": {"type": "string"},
                "frame": {
                    "type": "array",
                    "items": {"type": "number"},
                },
            },
            "required": ["frame", "sheet", "text"],
        },
        "Error": {
            "type": "object",
            "title": "Error",
            "additionalProperties": False,
            "properties": {
                "message": {"type": "string"},
                "errors": {"type": "object"},
            },
            "required": ["message"],
        },
    },
}


EXPECTED_SWAGGER_V3 = {
    "openapi": "3.1.0",
    "info": {"title": "My API", "version": "1.0.0", "description": ""},
    "security": [{"default": []}],
    "paths": {
        "/albums/{album_uid}": {
            "parameters": [
                {
                    "name": "album_uid",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "style": "simple",
                }
            ],
            "get": {
                "operationId": "get_album",
                "description": "Get an album by UID",
                "responses": {
                    "200": {
                        "description": "Album schema using DeepFriedMarshmallow's JitSchema with nested schema.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AlbumSchema"}
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
                "operationId": "update_album",
                "description": "Update an album",
                "responses": {
                    "200": {
                        "description": "Album schema using DeepFriedMarshmallow's JitSchema with nested schema.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AlbumSchema"}
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
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/AlbumUpdateSchema"
                            }
                        }
                    },
                },
                "security": [{"sharedSecret": []}],
            },
        },
        "/artists/{artist_uid}": {
            "parameters": [
                {
                    "name": "artist_uid",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "style": "simple",
                }
            ],
            "get": {
                "operationId": "get_artist",
                "description": "Get an artist by UID",
                "responses": {
                    "200": {
                        "description": "Artist schema using DeepFriedMarshmallow's JitSchema.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ArtistSchema"}
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
            },
        },
        "/sheets": {
            "get": {
                "operationId": "get_sheets",
                "description": "Get multiple sheets - tests List field with many=True",
                "responses": {
                    "200": {
                        "description": "Schema with List field to test deepcopy recursion fix.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/CompressedSheetText"},
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
            },
        },
    },
    "components": {
        "securitySchemes": {
            "sharedSecret": {"type": "apiKey", "in": "header", "name": "x-auth"},
            "default": {"type": "apiKey", "in": "header", "name": "x-another"},
        },
        "schemas": {
            "AlbumSchema": {
                "type": "object",
                "title": "AlbumSchema",
                "additionalProperties": False,
                "description": "Album schema using DeepFriedMarshmallow's JitSchema with nested schema.",
                "properties": {
                    "title": {"type": "string"},
                    "release_date": {"type": "string", "format": "date"},
                    "artist": {"$ref": "#/components/schemas/ArtistSchema"},
                },
            },
            "AlbumUpdateSchema": {
                "type": "object",
                "title": "AlbumUpdateSchema",
                "additionalProperties": False,
                "description": "Schema for updating album - partial fields.",
                "properties": {
                    "title": {"type": "string"},
                },
            },
            "ArtistSchema": {
                "type": "object",
                "title": "ArtistSchema",
                "additionalProperties": False,
                "description": "Artist schema using DeepFriedMarshmallow's JitSchema.",
                "properties": {
                    "name": {"type": "string"},
                },
            },
            "CompressedSheetText": {
                "type": "object",
                "title": "CompressedSheetText",
                "additionalProperties": False,
                "description": "Schema with List field to test deepcopy recursion fix.",
                "properties": {
                    "sheet": {"type": "string", "format": "uuid"},
                    "text": {"type": "string"},
                    "frame": {
                        "type": "array",
                        "items": {"type": "number"},
                    },
                },
                "required": ["frame", "sheet", "text"],
            },
            "Error": {
                "type": "object",
                "title": "Error",
                "additionalProperties": False,
                "properties": {
                    "message": {"type": "string"},
                    "errors": {"type": "object"},
                },
                "required": ["message"],
            },
        },
    },
}
