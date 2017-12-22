from __future__ import unicode_literals

import os

from plangrid.flask_toolbox.config_parser import ConfigParser


_extensions = {}


class DependencyError(Exception):
    pass


class Extension(object):
    NAME = None
    DEPENDENCIES = tuple()

    def __init__(self, app=None, config=None):
        self.config = config or {}

        if app is not None:
            self.init_app(app, self.config)

    @property
    def name(self):
        if not self.NAME:
            raise Exception('Extension must have a NAME!')

    def add_params_to_parser(self, parser):
        """
        Adds configuration parameters for the extension.

        Implement this method if your extension needs parameters.

        :param ConfigParser parser:
        """
        pass

    def init_extension(self, app, config):
        """
        Implement the extension initialization here.

        :param flask.Flask app:
        :param dict config:
        """
        raise NotImplemented

    def _resolve_config(self, app, config):
        """
        Resolves the configuration parameters for the extension.

        :param flask.Flask app:
        :param dict config:
        :rtype: config
        """
        config = config or {}

        parser = ConfigParser()
        self.add_params_to_parser(parser)

        return parser.resolve(sources=(
            config,
            self.config,
            app.config,
            os.environ
        ))

    def _check_extension_dependencies(self, app):
        missing_dependencies = \
            set(d.name for d in self.DEPENDENCIES) - _extensions[app]

        if missing_dependencies:
            raise DependencyError(
                'The {} extension depends on the following extensions: {}'.format(
                    self.name,
                    ', '.join(missing_dependencies)
                )
            )

    def _register_extension(self, app):
        _extensions[app].add(self.name)

    def init_app(self, app, config=None):
        resolved_config = self._resolve_config(
            app=app,
            config=config
        )

        self._check_extension_dependencies(app=app)
        self._register_extension(app=app)

        self.init_extension(
            app=app,
            config=resolved_config
        )
