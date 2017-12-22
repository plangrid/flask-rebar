from __future__ import unicode_literals

import bugsnag
import bugsnag.flask as bugsnag_flask

from plangrid.flask_toolbox.extensions.extension import Extension


class Bugsnag(Extension):
    def add_params_to_parser(self, parser):
        parser.add_param(name='BUGSNAG_API_KEY')
        parser.add_param(name='BUGSNAG_RELEASE_STAGE')

    def init_extension(self, app, config):
        if config['BUGSNAG_API_KEY'] is not None:
            bugsnag.configure(
                api_key=config['BUGSNAG_API_KEY'],
                release_stage=config['BUGSNAG_RELEASE_STAGE']
            )
            bugsnag_flask.handle_exceptions(app)
