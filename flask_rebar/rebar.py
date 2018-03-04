"""
    Rebar Extension
    ~~~~~~~~~~~~~~~

    The main entry point for Flask-Rebar, including a Flask extension
    and a registry for request handlers.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals

import sys
from collections import defaultdict
from collections import namedtuple
from copy import copy
from functools import wraps

import marshmallow
from flask import current_app, jsonify
from flask import g
from flask import request

from flask_rebar import messages
from flask_rebar.authenticators import USE_DEFAULT
from flask_rebar import errors
from flask_rebar.request_utils import marshal
from flask_rebar.request_utils import response
from flask_rebar.request_utils import get_header_params_or_400
from flask_rebar.request_utils import get_json_body_params_or_400
from flask_rebar.request_utils import get_query_string_params_or_400
from flask_rebar.swagger_generation import SwaggerV2Generator
from flask_rebar.swagger_ui import create_swagger_ui_blueprint

# Metadata about a declared handler function. This can be used to both
# declare the flask routing and to autogenerate swagger.
PathDefinition = namedtuple('PathDefinition', [
    'func',
    'path',
    'method',
    'endpoint',
    'marshal_schema',
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
        marshal_schema=None
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

        if marshal_schema:
            if isinstance(rv, tuple):
                data, status_code = rv[0], rv[1]
            else:
                data, status_code = rv, 200

            try:
                schema = marshal_schema[status_code]
            except KeyError:
                raise

            if schema is None:
                # Allow for the schema to be declared as None, which allows
                # for status codes with no bodies (i.e. a 204 status code)
                return response(
                    data=data, status_code=status_code
                )

            marshaled = marshal(
                data=data,
                schema=schema
            )

            return response(
                data=marshaled,
                status_code=status_code
            )

        else:
            return rv

    return wrapped


def get_validated_body():
    """
    Retrieve the result of validating/transforming an incoming request body with
    the `request_body_schema` a handler was registered with.

    :rtype: dict
    """
    return g.validated_body


def get_validated_args():
    """
    Retrieve the result of validating/transforming an incoming request's query
    string with the `query_string_schema` a handler was registered with.

    :rtype: dict
    """
    return g.validated_args


def get_validated_headers():
    """
    Retrieve the result of validating/transforming an incoming request's headers
    with the `headers_schema` a handler was registered with.

    :rtype: dict
    """
    return g.validated_headers


def normalize_prefix(prefix):
    """
    Removes slashes from a URL path prefix.

    :param str prefix:
    :rtype: str
    """
    if prefix and prefix.startswith('/'):
        prefix = prefix[1:]
    if prefix and prefix.endswith('/'):
        prefix = prefix[:-1]

    return prefix


def prefix_url(prefix, url):
    """
    Returns a new URL with the prefix prepended to the provided URL.

    :param str prefix:
    :param str url:
    :rtype: str
    """
    prefix = normalize_prefix(prefix)
    url = url[1:] if url.startswith('/') else url
    return '/{}/{}'.format(prefix, url)


class HandlerRegistry(object):
    """
    Registry for request handlers.

    This should typically be instantiated via a :class:`Rebar` instance::

        rebar = Rebar()
        registry = rebar.create_handler_registry()

    Although it can be instantiated independently and added to the registry::

        rebar = Rebar()
        registry = HandlerRegistry()
        rebar.add_handler_registry(registry)

    :param str prefix:
        URL prefix for all handlers registered with this registry instance.
    :param flask_rebar.authenticators.Authenticator default_authenticator:
        Authenticator to use for all handlers as a default.
    :param marshmallow.Schema default_headers_schema:
        Schema to validate the headers on all requests as a default.
    :param swagger_generator:
        Object to generate a Swagger specification from this registry. This will be
        the Swagger generator that is used in the endpoints swagger and swagger UI
        that are added to the API.
        If left as None, a `SwaggerV2Generator` instance will be used.
    :param str swagger_path:
        The Swagger specification as a JSON document will be hosted at this URL.
        If set as None, no swagger specification will be hosted.
    :param str swagger_ui_path:
        The HTML Swagger UI will be hosted at this URL.
        If set as None, no Swagger UI will be hosted.
    """

    def __init__(
            self,
            prefix=None,
            default_authenticator=None,
            default_headers_schema=None,
            swagger_generator=None,
            swagger_path='/swagger',
            swagger_ui_path='/swagger/ui'
    ):
        self.prefix = normalize_prefix(prefix)
        self._paths = defaultdict(dict)
        self.default_authenticator = default_authenticator
        self.default_headers_schema = default_headers_schema
        self.swagger_generator = swagger_generator or SwaggerV2Generator()
        self.swagger_path = swagger_path
        self.swagger_ui_path = swagger_ui_path

    def set_default_authenticator(self, authenticator):
        """
        Sets a handler authenticator to be used by default.

        :param flask_rebar.authenticators.Authenticator authenticator:
        """
        self.default_authenticator = authenticator

    def set_default_headers_schema(self, headers_schema):
        """
        Sets the schema to be used by default to validate incoming headers.

        :param marshmallow.Schema headers_schema:
        """
        self.default_headers_schema = headers_schema

    def clone(self):
        """
        Returns a new, shallow-copied instance of :class:`HandlerRegistry`.

        :rtype: HandlerRegistry
        """
        return copy(self)

    def _prefixed(self, path):
        if self.prefix:
            return prefix_url(prefix=self.prefix, url=path)
        else:
            return path

    def _prefixed_swagger_path(self):
        return self._prefixed(self.swagger_path)

    def _prefixed_swagger_ui_path(self):
        return self._prefixed(self.swagger_ui_path)

    @property
    def paths(self):
        # We duplicate the paths so we can modify the path definitions right before
        # they are accessed.
        paths = defaultdict(dict)

        for path, methods in self._paths.items():
            for method, definition_ in methods.items():
                path = definition_.path

                if self.prefix:
                    path = prefix_url(prefix=self.prefix, url=path)

                paths[path][method] = PathDefinition(
                    func=definition_.func,
                    path=path,
                    method=definition_.method,
                    endpoint=definition_.endpoint,
                    marshal_schema=definition_.marshal_schema,
                    query_string_schema=definition_.query_string_schema,
                    request_body_schema=definition_.request_body_schema,
                    headers_schema=definition_.headers_schema,
                    authenticator=definition_.authenticator,
                )

        return paths

    def add_handler(
            self,
            func,
            rule,
            method='GET',
            endpoint=None,
            marshal_schema=None,
            query_string_schema=None,
            request_body_schema=None,
            headers_schema=USE_DEFAULT,
            authenticator=USE_DEFAULT
    ):
        """
        Registers a function as a request handler.

        :param func:
            The Flask "view_func"
        :param str rule:
            The Flask "rule"
        :param str method:
            The HTTP method this handler accepts
        :param str endpoint:
        :param dict[int, marshmallow.Schema] marshal_schema:
            Dictionary mapping response codes to schemas to use to marshal
            the response. For now this assumes everything is JSON.
        :param marshmallow.Schema query_string_schema:
            Schema to use to deserialize query string arguments.
        :param marshmallow.Schema request_body_schema:
            Schema to use to deserialize the request body. For now this
            assumes everything is JSON.
        :param Type[USE_DEFAULT]|None|marshmallow.Schema headers_schema:
            Schema to use to grab and validate headers.
        :param Type[USE_DEFAULT]|None|flask_rebar.framing.authenticators.Authenticator authenticator:
            An authenticator object to authenticate incoming requests.
            If left as USE_DEFAULT, the Rebar's default will be used.
            Set to None to make this an unauthenticated handler.
        """
        if isinstance(marshal_schema, marshmallow.Schema):
            marshal_schema = {200: marshal_schema}

        self._paths[rule][method] = PathDefinition(
            func=func,
            path=rule,
            method=method,
            endpoint=endpoint,
            marshal_schema=marshal_schema,
            query_string_schema=query_string_schema,
            request_body_schema=request_body_schema,
            headers_schema=headers_schema,
            authenticator=authenticator,
        )

    def handles(
            self,
            rule,
            method='GET',
            endpoint=None,
            marshal_schema=None,
            query_string_schema=None,
            request_body_schema=None,
            headers_schema=USE_DEFAULT,
            authenticator=USE_DEFAULT
    ):
        """
        Same arguments as :meth:`HandlerRegistry.add_handler`, except this can
        be used as a decorator.
        """

        def wrapper(f):
            self.add_handler(
                func=f,
                rule=rule,
                method=method,
                endpoint=endpoint,
                marshal_schema=marshal_schema,
                query_string_schema=query_string_schema,
                request_body_schema=request_body_schema,
                headers_schema=headers_schema,
                authenticator=authenticator
            )
            return f

        return wrapper

    def register(self, app):
        self._register_routes(app=app)
        self._register_swagger(app=app)
        self._register_swagger_ui(app=app)

    def _register_routes(self, app):
        for path, methods in self.paths.items():
            for method, definition_ in methods.items():
                if definition_.endpoint:
                    endpoint = definition_.endpoint
                else:
                    endpoint = definition_.func.__name__

                if self.prefix:
                    endpoint = '.'.join((self.prefix, endpoint))

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
                        marshal_schema=definition_.marshal_schema
                    ),
                    methods=[definition_.method],
                    endpoint=endpoint
                )

    def _register_swagger(self, app):
        swagger_endpoint = 'get_swagger'

        if self.prefix:
            swagger_endpoint = '.'.join((self.prefix, swagger_endpoint))

        if self.swagger_path:
            @app.route(self._prefixed_swagger_path(), methods=['GET'], endpoint=swagger_endpoint)
            def get_swagger():
                swagger = self.swagger_generator.generate(
                    registry=self,
                    host=request.host
                )
                return response(data=swagger)

    def _register_swagger_ui(self, app):
        blueprint_name = 'swagger_ui'

        if self.prefix:
            blueprint_name = self.prefix + blueprint_name

        if self.swagger_ui_path:
            blueprint = create_swagger_ui_blueprint(
                name=blueprint_name,
                ui_url=self._prefixed_swagger_ui_path(),
                swagger_url=self._prefixed_swagger_path(),
            )
            app.register_blueprint(
                blueprint=blueprint,
                url_prefix=self._prefixed_swagger_ui_path(),
            )


class Rebar(object):
    """
    The main entry point for the Flask-Rebar extension.

    This registers handler registries with the Flask application and initializes
    all the Flask-Rebar goodies.

    Example usage::

        app = Flask(__name__)
        rebar = Rebar()
        registry = rebar.create_handler_registry()

        @registry.handles()
        def handler():
            ...

        rebar.init_app(app)

    """

    def __init__(self):
        self.handler_registries = set()
        self.paths = defaultdict(dict)
        self.uncaught_exception_handlers = []

    def create_handler_registry(
            self,
            prefix=None,
            default_authenticator=None,
            default_headers_schema=None,
            swagger_generator=None,
            swagger_path='/swagger',
            swagger_ui_path='/swagger/ui',
    ):
        """
        Create a new handler registry and add to this extension's set of
        registered registries.

        When calling :meth:`Rebar.init_app`, all registries created via this method
        will be registered with the Flask application.

        Parameters are the same for the :class:`HandlerRegistry` constructor.

        :rtype: HandlerRegistry
        """
        registry = HandlerRegistry(
            prefix=prefix,
            default_authenticator=default_authenticator,
            default_headers_schema=default_headers_schema,
            swagger_generator=swagger_generator,
            swagger_path=swagger_path,
            swagger_ui_path=swagger_ui_path,
        )
        self.add_handler_registry(registry=registry)
        return registry

    def add_handler_registry(self, registry):
        """
        Register a handler registry with the extension.

        There is no need to call this if a handler registry was created
        via :meth:`Rebar.create_handler_registry`.

        :param HandlerRegistry registry:
        """
        self.handler_registries.add(registry)

    @property
    def validated_body(self):
        """
        Proxy to the result of validating/transforming an incoming request body with
        the `request_body_schema` a handler was registered with.

        :rtype: dict
        """
        return get_validated_body()

    @property
    def validated_args(self):
        """
        Proxy to the result of validating/transforming an incoming request's query
        string with the `query_string_schema` a handler was registered with.

        :rtype: dict
        """
        return get_validated_args()

    @property
    def validated_headers(self):
        """
        Proxy to the result of validating/transforming an incoming request's headers
        with the `headers_schema` a handler was registered with.

        :rtype: dict
        """
        return get_validated_headers()

    def add_uncaught_exception_handler(self, func):
        """
        Add a function that will be called for uncaught exceptions, i.e. exceptions
        that will result in a 500 error.

        This function should accept the exception instance as a single positional argument.

        All handlers will be called in the order they are added.

        :param Callable func:
        """
        self.uncaught_exception_handlers.append(func)

    def init_app(self, app):
        """
        Register all the handler registries with a Flask application.

        :param flask.Flask app:
        """
        self._init_error_handling(app=app)

        for registry in self.handler_registries:
            registry.register(app=app)

    def _init_error_handling(self, app):
        @app.errorhandler(errors.HttpJsonError)
        def handle_http_error(error):
            return self._create_json_error_response(
                message=error.error_message,
                http_status_code=error.http_status_code,
                additional_data=error.additional_data
            )

        @app.errorhandler(404)
        @app.errorhandler(405)
        def handle_werkzeug_http_error(error):
            return self._create_json_error_response(
                message=error.description,
                http_status_code=error.code
            )

        @app.errorhandler(Exception)
        def handle_werkzeug_http_error(error):
            exc_info = sys.exc_info()
            current_app.log_exception(exc_info=exc_info)

            for func in self.uncaught_exception_handlers:
                func(error)

            return self._create_json_error_response(
                message=messages.internal_server_error,
                http_status_code=500
            )

    def _create_json_error_response(
            self,
            message,
            http_status_code,
            additional_data=None
    ):
        """
        Compiles a response object for an error.

        :param str message:
        :param int http_status_code:
          An optional, application-specific error code to add to the response.
        :param additional_data:
          Additional JSON data to attach to the response.
        :rtype: flask.Response
        """
        body = {'message': message}
        if additional_data:
            body.update(additional_data)
        resp = jsonify(body)
        resp.status_code = http_status_code
        return resp
