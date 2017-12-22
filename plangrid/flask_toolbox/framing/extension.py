from __future__ import unicode_literals

from collections import defaultdict
from collections import namedtuple
from functools import wraps

import marshmallow
from flask import request
from flask import g
from flask_swagger_ui import get_swaggerui_blueprint

from plangrid.flask_toolbox.framing.authenticators import USE_DEFAULT
from plangrid.flask_toolbox.framing.swagger_generator import SwaggerV2Generator
from plangrid.flask_toolbox import get_json_body_params_or_400,\
    get_query_string_params_or_400, get_header_params_or_400
from plangrid.flask_toolbox.request_utils import marshal
from plangrid.flask_toolbox.request_utils import response
from plangrid.flask_toolbox.extension import Extension
from plangrid.flask_toolbox.errors import Errors


# Metadata about a declared handler function. This can be used to both
# declare the flask routing and to autogenerate swagger.
PathDefinition = namedtuple('PathDefinition', [
    'func',
    'path',
    'method',
    'endpoint',
    'marshal_schemas',
    'query_string_schema',
    'request_body_schema',
    'headers_schema',
    'authenticator'
])


def _wrap_handler(
        f,
        authenticator=None,
        query_string_schema=None,
        request_body_schema=None,
        headers_schema=None,
        marshal_schemas=None
):
    """
    Wraps a handler function before registering it with a Flask application.

    :param f:
    :returns: a new, wrapped handler function
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if authenticator:
            authenticator.authenticate()

        if query_string_schema:
            g.validated_args = get_query_string_params_or_400(
                schema=query_string_schema
            )

        if request_body_schema:
            g.validated_body = get_json_body_params_or_400(
                schema=request_body_schema
            )

        if headers_schema:
            g.validated_headers = get_header_params_or_400(
                schema=headers_schema
            )

        rv = f(*args, **kwargs)

        if marshal_schemas:
            if isinstance(rv, tuple):
                data, status_code = rv[0], rv[1]
            else:
                data, status_code = rv, 200

            try:
                marshal_schema = marshal_schemas[status_code]
            except KeyError:
                raise

            if marshal_schema is None:
                # Allow for the schema to be declared as None, which allows
                # for status codes with no bodies (i.e. a 204 status code)
                return response(
                    data=data, status_code=status_code
                )

            marshaled = marshal(
                data=data,
                schema=marshal_schema
            )

            return response(
                data=marshaled,
                status_code=status_code
            )

        else:
            return rv

    return wrapped


class Framer(Extension):
    """
    Declaratively constructs a REST API.

    Similar to a Flask Blueprint, but intentionally kept separate.
    """
    NAME = 'ToolboxExtension::Framer'
    DEPENDENCIES = (Errors,)

    def add_params_to_parser(self, parser):
        parser.add_param(name='TOOLBOX_FRAMER_SWAGGER_PATH', default='/swagger')
        parser.add_param(name='TOOLBOX_FRAMER_SWAGGER_UI_PATH', default='/swagger/ui')

    def __init__(
            self,
            default_authenticator=None,
            default_headers_schema=None,
            swagger_generator=None,
            swagger_ui_config=None,
            config=None
    ):
        self.paths = defaultdict(dict)
        self.default_authenticator = default_authenticator
        self.swagger_generator = swagger_generator or SwaggerV2Generator()
        self.swagger_ui_config = swagger_ui_config or {}
        self.default_headers_schema = default_headers_schema

        super(Framer, self).__init__(config=config)

    @property
    def validated_body(self):
        return g.validated_body

    @property
    def validated_args(self):
        return g.validated_args

    @property
    def validated_headers(self):
        return g.validated_headers

    def set_default_authenticator(self, authenticator):
        """
        Sets a handler authenticator to be used by default.

        :param plangrid.flask_toolbox.framing.authenticators.Authenticator authenticator:
        """
        self.default_authenticator = authenticator

    def set_default_headers_schema(self, headers_schema):
        """
        Sets the schema to be used by default to validate incoming headers.

        :param marshmallow.Schema headers_schema:
        """
        self.default_headers_schema = headers_schema

    def add_handler(
            self,
            func,
            path,
            method='GET',
            endpoint=None,
            marshal_schemas=None,
            query_string_schema=None,
            request_body_schema=None,
            headers_schema=USE_DEFAULT,
            authenticator=USE_DEFAULT
    ):
        """
        Registers a function as a request handler.

        :param func:
            The Flask "view_func"
        :param str path:
            The Flask "rule"
        :param str method:
            The HTTP method this handler accepts
        :param str endpoint:
        :param dict[int, marshmallow.Schema] marshal_schemas:
            Dictionary mapping response codes to schemas to use to marshal
            the response. For now this assumes everything is JSON.
        :param marshmallow.Schema query_string_schema:
            Schema to use to deserialize query string arguments.
        :param marshmallow.Schema request_body_schema:
            Schema to use to deserialize the request body. For now this
            assumes everything is JSON.
        :param Type[USE_DEFAULT]|None|marshmallow.Schema headers_schema:
            Schema to use to grab and validate headers.
        :param Type[USE_DEFAULT]|None|plangrid.flask_toolbox.framing.authenticators.Authenticator authenticator:
            An authenticator object to authenticate incoming requests.
            If left as USE_DEFAULT, the Framer's default will be used.
            Set to None to make this an unauthenticated handler.
        """
        if isinstance(marshal_schemas, marshmallow.Schema):
            marshal_schemas = {200: marshal_schemas}

        self.paths[path][method] = PathDefinition(
            func=func,
            path=path,
            method=method,
            endpoint=endpoint,
            marshal_schemas=marshal_schemas,
            query_string_schema=query_string_schema,
            request_body_schema=request_body_schema,
            headers_schema=headers_schema,
            authenticator=authenticator,
        )

    def handles(
            self,
            path,
            method='GET',
            endpoint=None,
            marshal_schemas=None,
            query_string_schema=None,
            request_body_schema=None,
            headers_schema=USE_DEFAULT,
            authenticator=USE_DEFAULT
    ):
        """
        Same arguments as `add_handler`, except this can be used as a decorator.
        """
        def wrapper(f):
            self.add_handler(
                func=f,
                path=path,
                method=method,
                endpoint=endpoint,
                marshal_schemas=marshal_schemas,
                query_string_schema=query_string_schema,
                request_body_schema=request_body_schema,
                headers_schema=headers_schema,
                authenticator=authenticator
            )
            return f
        return wrapper

    def init_extension(self, app, config):
        """Registers all the handlers with a Flask application."""

        for path, methods in self.paths.items():
            for method, definition_ in methods.items():
                app.add_url_rule(
                    rule=definition_.path,
                    view_func=_wrap_handler(
                        f=definition_.func,
                        authenticator=(
                            self.default_authenticator
                            if definition_.authenticator is USE_DEFAULT
                            else definition_.authenticator
                        ),
                        query_string_schema=definition_.query_string_schema,
                        request_body_schema=definition_.request_body_schema,
                        headers_schema=(
                            self.default_headers_schema
                            if definition_.headers_schema is USE_DEFAULT
                            else definition_.headers_schema
                        ),
                        marshal_schemas=definition_.marshal_schemas
                    ),
                    methods=[definition_.method],
                    endpoint=definition_.endpoint
                )

        swagger_path = config['TOOLBOX_FRAMER_SWAGGER_PATH']
        swagger_ui_path = config['TOOLBOX_FRAMER_SWAGGER_UI_PATH']

        @app.route(swagger_path, methods=['GET'])
        def get_swagger():
            swagger = self.swagger_generator.generate(
                framer=self,
                host=request.host
            )
            return response(data=swagger)

        swagger_ui_blueprint = get_swaggerui_blueprint(
            base_url=swagger_ui_path,
            api_url=swagger_path,
            config=self.swagger_ui_config,
        )
        app.register_blueprint(
            blueprint=swagger_ui_blueprint,
            url_prefix=swagger_ui_path,
        )
