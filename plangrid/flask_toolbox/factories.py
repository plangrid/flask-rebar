from plangrid.flask_toolbox.errors import Errors
from plangrid.flask_toolbox.healthcheck import Healthcheck
from plangrid.flask_toolbox.url_converters import UrlConverters
from plangrid.flask_toolbox.pagination import Pagination
from plangrid.flask_toolbox.bugsnag import Bugsnag
from plangrid.flask_toolbox.framing import HeaderApiKeyAuthenticator
from plangrid.flask_toolbox.toolbox import Toolbox
from plangrid.flask_toolbox.constants import HEADER_AUTH_TOKEN


def init_toolbox(app, config=None):
    Errors(app=app, config=config)
    Healthcheck(app=app, config=config)
    UrlConverters(app=app, config=config)
    Pagination(app=app, config=config)
    Bugsnag(app=app, config=config)
    Toolbox(app=app, config=config)


def init_framer(app, framer, config=None):
    Errors(app=app, config=config)
    Healthcheck(app=app, config=config)
    UrlConverters(app=app, config=config)
    Pagination(app=app, config=config)
    Bugsnag(app=app, config=config)

    authenticator = HeaderApiKeyAuthenticator(header=HEADER_AUTH_TOKEN)
    framer.set_default_authenticator(authenticator=authenticator)

    framer.init_app(app=app, config=config)

    return authenticator
