from __future__ import unicode_literals

import os

from plangrid.flask_toolbox.extensions.config_parser import ConfigParser


class Extension(object):
    def __init__(self, app=None, config=None):
        self.config = config or {}

        if app is not None:
            self.init_app(app, self.config)

    def add_params_to_parser(self, parser):
        pass

    def init_extension(self, app, config):
        raise NotImplemented

    def resolve_config(self, app, config):
        config = config or {}

        parser = ConfigParser()
        self.add_params_to_parser(parser)

        return parser.resolve(sources=(
            config,
            self.config,
            app.config,
            os.environ
        ))

    def init_app(self, app, config=None):
        resolved_config = self.resolve_config(
            app=app,
            config=config
        )

        self.init_extension(
            app=app,
            config=resolved_config
        )
