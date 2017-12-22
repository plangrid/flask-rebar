from __future__ import unicode_literals

from plangrid.flask_toolbox.framing.authenticators import HeaderApiKeyAuthenticator
from plangrid.flask_toolbox.framing.framer import Framer
from plangrid.flask_toolbox.toolbox import HEADER_AUTH_TOKEN
from plangrid.flask_toolbox.extensions.healthcheck import Healthcheck
from plangrid.flask_toolbox.extensions.bugsnag import Bugsnag
from plangrid.flask_toolbox.extensions.url_converters import UrlConverters
from plangrid.flask_toolbox.extensions.errors import Errors


class ToolboxFramer(Framer):
    """Framer pre-loaded with all the PlanGrid specific goodies."""

    def __init__(self, swagger_generator=None):
        authenticator = HeaderApiKeyAuthenticator(header=HEADER_AUTH_TOKEN)
        super(ToolboxFramer, self).__init__(
            default_authenticator=authenticator,
            swagger_generator=swagger_generator,
        )

    def register(self, app):
        super(ToolboxFramer, self).register(app)
        Healthcheck(app=app)
        Bugsnag(app=app)
        UrlConverters(app=app)
        Errors(app=app)

    def register_auth_key(self, key, app_name=HeaderApiKeyAuthenticator.DEFAULT_APP_NAME):
        self.default_authenticator.register_key(key=key, app_name=app_name)
