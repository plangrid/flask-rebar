from flask import Flask
from marshmallow import fields, pre_dump, pre_load

from flask_rebar import (
    Rebar,
    errors,
    HeaderApiKeyAuthenticator,
    Tag,
    SwaggerV2Generator,
)
from flask_rebar.validation import RequestSchema, ResponseSchema


rebar = Rebar()

# Rebar will create a default swagger generator if none is specified.
# However, if you want more control over how the swagger is generated, you can
# provide your own.
# Here we've specified additional metadata for operation tags.
generator = SwaggerV2Generator(
    tags=[Tag(name="todo", description="Operations for managing TODO items.")]
)

registry = rebar.create_handler_registry(
    swagger_generator=generator,
    handlers='todo.handlers',
)
