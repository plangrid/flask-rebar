from flask import Flask
from flask_rebar import HeaderApiKeyAuthenticator

from .rebar import rebar
from .rebar import registry


def create_app():
    app = Flask(__name__)

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
