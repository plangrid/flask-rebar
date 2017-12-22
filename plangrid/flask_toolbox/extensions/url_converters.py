from __future__ import unicode_literals

from plangrid.flask_toolbox.converters import UUIDStringConverter
from plangrid.flask_toolbox.extensions.extension import Extension


class UrlConverters(Extension):
    def init_extension(self, app, config):
        app.url_map.converters['uuid_string'] = UUIDStringConverter
