from __future__ import unicode_literals

import uuid
import warnings

from flask import Request
from flask import g

from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.errors import http_errors
from plangrid.flask_toolbox.extension import Extension
from plangrid.flask_toolbox import constants
from plangrid.flask_toolbox.errors import Errors


class ToolboxRequest(Request):
    """Lightly wraps flask.Request to getters for PlanGrid specific headers."""
    @property
    def user_id(self):
        return self.headers.get(constants.HEADER_USER_ID)

    @property
    def request_id(self):
        return self.headers.get(constants.HEADER_REQUEST_ID, str(uuid.uuid4()))

    @property
    def auth_token(self):
        return self.headers.get(constants.HEADER_AUTH_TOKEN)

    @property
    def application_id(self):
        return self.headers.get(constants.HEADER_APPLICATION_ID)

    @property
    def scopes(self):
        scopes_string = self.headers.get(constants.HEADER_SCOPES, '').strip()
        if scopes_string:
            scopes_split = [
                s.strip()
                for s in scopes_string.split(' ')
                if s
            ]
            return set(scopes_split)
        else:
            return set()

    def on_json_loading_failed(self, e):
        raise http_errors.BadRequest(messages.invalid_json)


class Toolbox(Extension):
    NAME = 'ToolboxExtension::OriginalGangster'
    DEPENDENCIES = (Errors,)

    def __init__(self, *args, **kwargs):
        warnings.warn(
            'The Toolbox is deprecated. Start using the Framer!',
            DeprecationWarning
        )
        super(Toolbox, self).__init__(*args, **kwargs)

    def add_params_to_parser(self, parser):
        parser.add_param(name='TOOLBOX_AUTH_TOKEN')

    def init_extension(self, app, config):
        def set_auth_token():
            g.toolbox_auth_token = config['TOOLBOX_AUTH_TOKEN']

        app.before_request(set_auth_token)

        # Set the flask.request proxy to our extended type
        app.request_class = ToolboxRequest
