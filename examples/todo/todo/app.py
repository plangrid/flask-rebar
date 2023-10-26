from flask import Flask
from flask_rebar import HeaderApiKeyAuthenticator
from marshmallow import fields, pre_dump, pre_load

from flask_rebar import (
    Rebar,
    errors,
    HeaderApiKeyAuthenticator,
    Tag,
    SwaggerV2Generator,
)
from flask_rebar.validation import RequestSchema, ResponseSchema

from .converters import TodoTypeConverter


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
    handlers="todo.handlers",
)


def create_app():
    app = Flask(__name__)

    # register new type for url mapping
    app.url_map.converters["todo_types"] = TodoTypeConverter
    generator.register_flask_converter_to_swagger_type("todo_types", TodoTypeConverter)

    authenticator = HeaderApiKeyAuthenticator(header="X-MyApp-Key")
    # The HeaderApiKeyAuthenticator does super simple authentication, designed for
    # service-to-service authentication inside of a protected network, by looking for a
    # shared secret in the specified header. Here we define what that shared secret is.
    authenticator.register_key(key="my-api-key")
    registry.set_default_authenticator(authenticator=authenticator)

    rebar.init_app(app=app)

    return app


if __name__ == "__main__":
    create_app().run()
