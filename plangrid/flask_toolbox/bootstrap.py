from plangrid.flask_toolbox.errors import Errors
from plangrid.flask_toolbox.healthcheck import Healthcheck
from plangrid.flask_toolbox.url_converters import UrlConverters
from plangrid.flask_toolbox.pagination import Pagination
from plangrid.flask_toolbox.bugsnag import Bugsnag
from plangrid.flask_toolbox.framing import HeaderApiKeyAuthenticator
from plangrid.flask_toolbox.toolbox import Toolbox
from plangrid.flask_toolbox.constants import HEADER_AUTH_TOKEN


def bootstrap_app_with_toolbox(app, config=None):
    """
    DEPRECATED

    Initializes the recommended set of flask-toolbox extensions and
    registers them with a Flask application.

    Deprecated in favor of `bootstrap_app_with_framer`.

    :param flask.Flask app:
    :param dict config:
    """
    Errors(app=app, config=config)
    Healthcheck(app=app, config=config)
    UrlConverters(app=app, config=config)
    Pagination(app=app, config=config)
    Bugsnag(app=app, config=config)
    Toolbox(app=app, config=config)


def bootstrap_app_with_framer(app, framer, config=None):
    """
    Initializes the recommended set of flask-toolbox extensions and
    registers them with a Flask application.

    This also configures a Framer with the recommended authentication
    mechanism and registers it with the application.

    This should be called at application startup, for example::

        from flask import Flask
        from plangrid.flask_toolbox import Framer

        framer = Framer()

        @framer.handles('/')
        def hello_world():
            return 'Hello, world!'

        app = Flask(__name__)

        bootstrap_app_with_framer(
            app=app,
            framer=framer,
            config={'TOOLBOX_FRAMER_SWAGGER_UI_PATH': '/swagger-ui'}
        )

        framer.default_authenticator.register_key(key='my-api-key')

        app.run()

    :param flask.Flask app:
    :param plangrid.flask_toolbox.Framer framer:
    :param dict config: Dictionary with configuration parameters that is passed
        to every extension, overriding the values found in environment variables
    """
    Errors(app=app, config=config)
    Healthcheck(app=app, config=config)
    UrlConverters(app=app, config=config)
    Pagination(app=app, config=config)
    Bugsnag(app=app, config=config)

    authenticator = HeaderApiKeyAuthenticator(header=HEADER_AUTH_TOKEN)
    framer.set_default_authenticator(authenticator=authenticator)

    framer.init_app(app=app, config=config)
