from __future__ import unicode_literals

from flask import jsonify

from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.extension import Extension


HEALTHCHECK_ENDPOINT = 'health'


class Healthcheck(Extension):
    NAME = 'ToolboxExtension::Healthcheck'

    def init_extension(self, app, config):
        @app.route('/health', endpoint=HEALTHCHECK_ENDPOINT)
        def handle_healthcheck():
            return jsonify({'message': messages.health_check_response})
