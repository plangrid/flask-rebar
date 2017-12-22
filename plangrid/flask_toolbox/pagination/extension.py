from __future__ import unicode_literals

from flask import g

from plangrid.flask_toolbox.extension import Extension


DEFAULT_PAGINATION_LIMIT_MAX = 100


class Pagination(Extension):
    NAME = 'ToolboxExtension::Pagination'

    def add_params_to_parser(self, parser):
        parser.add_param(
            name='TOOLBOX_PAGINATION_LIMIT_MAX',
            coerce=int,
            default=DEFAULT_PAGINATION_LIMIT_MAX
        )

    def set_pagination_limit_max(self):
        g.pagination_limit_max = self.limit_max

    def init_extension(self, app, config):
        self.limit_max = config['TOOLBOX_PAGINATION_LIMIT_MAX']
        app.before_request(self.set_pagination_limit_max)
