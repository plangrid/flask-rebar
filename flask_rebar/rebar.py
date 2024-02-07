"""
    Rebar Extension
    ~~~~~~~~~~~~~~~

    The main entry point for Flask-Rebar, including a Flask extension
    and a registry for request handlers.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import annotations
import sys
from collections import defaultdict
from collections import namedtuple
from copy import copy
from functools import wraps
from flask import current_app, g, jsonify, request, Response
from flask.app import Flask
from marshmallow import Schema
from typing import (
    overload,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from typing_extensions import ParamSpec
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from werkzeug.routing import RequestRedirect
from werkzeug.utils import find_modules
from werkzeug.utils import import_string

from flask_rebar import messages
from flask_rebar import errors
from flask_rebar.authenticators import Authenticator
from flask_rebar.errors import HttpJsonError
from flask_rebar.messages import ErrorMessage
from flask_rebar.utils.defaults import USE_DEFAULT
from flask_rebar.utils.request_utils import marshal
from flask_rebar.utils.request_utils import response
from flask_rebar.utils.request_utils import get_header_params_or_400
from flask_rebar.utils.request_utils import get_json_body_params_or_400
from flask_rebar.utils.request_utils import get_query_string_params_or_400
from flask_rebar.utils.request_utils import normalize_schema
from flask_rebar.utils.deprecation import deprecated, deprecated_parameters
from flask_rebar.swagger_generation.swagger_generator_base import SwaggerGenerator
from flask_rebar.swagger_generation.swagger_generator_v2 import SwaggerV2Generator
from flask_rebar.swagger_ui import create_swagger_ui_blueprint


MOVED_PERMANENTLY_ERROR = RequestRedirect
PERMANENT_REDIRECT_ERROR = RequestRedirect

# for type hinting decorators
P = ParamSpec("P")
T = TypeVar("T")

JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
Data = Union[bytes, JsonType]


def _convert_authenticator_to_authenticators(
    authenticator: Optional[Union[Authenticator, Type[USE_DEFAULT]]]
) -> List[Union[Authenticator, Type[USE_DEFAULT]]]:
    if authenticator is None:
        return []
    elif isinstance(authenticator, Authenticator) or authenticator is USE_DEFAULT:
        return [authenticator]
    else:
        raise ValueError(
            "authenticator must be an instance of Authenticator, USE_DEFAULT, or None."
        )


def _unpack_view_func_return_value(
    rv: Union[
        Tuple[Data, int, Dict[str, str]],
        Tuple[Data, int],
        Tuple[Data, Dict[str, str]],
        Data,
    ],
) -> Tuple[
    Union[
        Tuple[Data, int, Dict[str, str]],
        Tuple[Data, int],
        Tuple[Data, Dict[str, str]],
        Data,
    ],
    int,
    Any,
]:
    """
    Normalize a return value from a view function into a tuple of (body, status, headers).

    This imitates Flask's own `Flask.make_response` method.

    :param rv: (body, status, headers), (body, status), (body, headers), or body
    :return: (body, status, headers)
    :rtype: tuple
    """
    headers: Any = {}
    data, status = rv, 200

    if isinstance(rv, tuple):
        if len(rv) == 3:
            data, status, headers = rv
        elif len(rv) == 2:
            if isinstance(rv[1], (Headers, dict, tuple, list)):
                data, headers = rv
            else:
                data, status = rv
        else:
            raise TypeError(
                "The view function did not return a valid response tuple."
                " The tuple must have the form (body, status, headers),"
                " (body, status), or (body, headers)."
            )

    return data, int(status), headers


def _wrap_handler(
    f: Callable[P, T],
    authenticators: Optional[List[Authenticator]] = None,
    query_string_schema: Optional[Schema] = None,
    request_body_schema: Optional[Schema] = None,
    headers_schema: Optional[Schema] = None,
    response_body_schema: Optional[Dict[int, Schema]] = None,
    mimetype: Optional[str] = None,
) -> Callable[P, Union[T, Response]]:
    """
    Wraps a handler function before registering it with a Flask application.

    :param f:
    :returns: a new, wrapped handler function
    """
    # authenticators can be a single Authenticator, a list of Authenticators, or None.
    if isinstance(authenticators, Authenticator):
        authenticators = [authenticators]

    @wraps(f)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> Union[T, Response]:
        if authenticators:
            first_error = None
            for authenticator in authenticators:
                try:
                    authenticator.authenticate()
                    break  # Short-circuit on first successful authentication
                except (errors.Unauthorized, errors.Forbidden) as e:
                    first_error = first_error or e
            else:
                raise first_error or errors.Unauthorized

        if query_string_schema:
            g.validated_args = get_query_string_params_or_400(
                schema=query_string_schema
            )

        if request_body_schema:
            g.validated_body = get_json_body_params_or_400(schema=request_body_schema)

        if headers_schema:
            g.validated_headers = get_header_params_or_400(schema=headers_schema)

        rv: Any = f(*args, **kwargs)

        if not response_body_schema:
            return rv

        if isinstance(rv, current_app.response_class):
            schema = response_body_schema[rv.status_code]
            # The schema may be set to None to bypass marshaling (e.g. for 204 responses).
            if schema is None:
                return rv
            # Otherwise, ensure the response body conforms to the promised schema.
            schema.loads(rv.data)  # May raise ValidationError.
            return rv

        data, status_code, headers = _unpack_view_func_return_value(rv)
        schema = response_body_schema[status_code]  # May raise KeyError.

        # The schema may be set to None to bypass marshaling (e.g. for 204 responses).
        if schema is None:
            return response(
                data=data, status_code=status_code, headers=headers, mimetype=mimetype
            )

        marshaled = marshal(data=data, schema=schema)
        return response(
            data=marshaled, status_code=status_code, headers=headers, mimetype=mimetype
        )

    return wrapped


def get_validated_body() -> Dict[str, Any]:
    """
    Retrieve the result of validating/transforming an incoming request body with
    the `request_body_schema` a handler was registered with.

    :rtype: dict
    """
    return g.validated_body


def get_validated_args() -> Dict[str, Any]:
    """
    Retrieve the result of validating/transforming an incoming request's query
    string with the `query_string_schema` a handler was registered with.

    :rtype: dict
    """
    return g.validated_args


def get_validated_headers() -> Dict[str, str]:
    """
    Retrieve the result of validating/transforming an incoming request's headers
    with the `headers_schema` a handler was registered with.

    :rtype: dict
    """
    return g.validated_headers


@overload
def normalize_prefix(prefix: str) -> str:
    ...


@overload
def normalize_prefix(prefix: None) -> None:
    ...


def normalize_prefix(prefix: Optional[str]) -> Optional[str]:
    """
    Removes slashes from a URL path prefix.

    :param str prefix:
    :rtype: str
    """
    if prefix and prefix.startswith("/"):
        prefix = prefix[1:]
    if prefix and prefix.endswith("/"):
        prefix = prefix[:-1]

    return prefix


def prefix_url(prefix: str, url: str) -> str:
    """
    Returns a new URL with the prefix prepended to the provided URL.

    :param str prefix:
    :param str url:
    :rtype: str
    """
    prefix = normalize_prefix(prefix)
    url = url[1:] if url.startswith("/") else url
    return f"/{prefix}/{url}"


# Metadata about a declared handler function. This can be used to both
# declare the flask routing and to autogenerate swagger.
class PathDefinition(
    namedtuple(
        "_PathDefinition",
        [
            "func",
            "path",
            "method",
            "endpoint",
            "response_body_schema",
            "query_string_schema",
            "request_body_schema",
            "headers_schema",
            "authenticators",
            "tags",
            "mimetype",
            "hidden",
            "summary",
        ],
    )
):
    __slots__ = ()

    @deprecated_parameters(
        authenticator=(
            "authenticators",
            "3.0",
            _convert_authenticator_to_authenticators,
        )
    )
    def __new__(cls, *args: Any, **kwargs: Any) -> "PathDefinition":
        return super().__new__(cls, *args, **kwargs)

    @property
    @deprecated("authenticator", "3.0")
    def authenticator(self) -> Optional[Authenticator]:
        return self.authenticators[0] if self.authenticators else None


class HandlerRegistry:
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
    :param Union(flask_rebar.authenticators.Authenticator, List(flask_rebar.authenticators.Authenticator), None)
        default_authenticators: List of Authenticators to use for all handlers as a default.
    :param marshmallow.Schema default_headers_schema:
        Schema to validate the headers on all requests as a default.
    :param str default_mimetype:
        Default response content-type if no content and not otherwise specified by the handler.
    :param flask_rebar.swagger_generation.swagger_generator.SwaggerGenerator swagger_generator:
        Object to generate a Swagger specification from this registry. This will be
        the Swagger generator that is used in the endpoints swagger and swagger UI
        that are added to the API.
        If left as None, a `SwaggerV2Generator` instance will be used.
    :param str spec_path:
        The Swagger specification as a JSON document will be hosted at this URL.
        If set as None, no swagger specification will be hosted.
    :param str spec_ui_path:
        The HTML Swagger UI will be hosted at this URL.
        If set as None, no Swagger UI will be hosted.
    :param list|str handlers:
         packages to search for modules where handlers are added for this registry.
    """

    @deprecated_parameters(
        default_authenticator=(
            "default_authenticators",
            "3.0",
            _convert_authenticator_to_authenticators,
        ),
        swagger_path="spec_path",  # we didn't specify an EOL for these two, maybe they just live forever (fine imho)
        swagger_ui_path="spec_ui_path",
    )
    def __init__(
        self,
        prefix: Optional[str] = None,
        default_authenticators: Union[Authenticator, List[Authenticator], None] = None,
        default_headers_schema: Optional[Schema] = None,
        default_mimetype: Optional[str] = None,
        swagger_generator: Optional[SwaggerGenerator] = None,
        spec_path: str = "/swagger",
        spec_ui_path: str = "/swagger/ui",
        handlers: Optional[Union[List[str], str]] = None,
    ) -> None:
        # default_authenticators can be a single Authenticator, a list of Authenticators, or None.
        if isinstance(default_authenticators, Authenticator):
            default_authenticators = [default_authenticators]
        elif default_authenticators is None:
            default_authenticators = []

        self.prefix = normalize_prefix(prefix)
        self._paths: Dict[str, Dict[str, PathDefinition]] = defaultdict(dict)
        self.default_authenticators = default_authenticators
        self.default_headers_schema = default_headers_schema
        self.default_mimetype = default_mimetype
        self.swagger_generator = swagger_generator or SwaggerV2Generator()
        self.spec_path = spec_path
        self.spec_ui_path = spec_ui_path
        if handlers is None:
            self.handlers: List[str] = []
        else:
            self.handlers = handlers if isinstance(handlers, list) else [handlers]

    @property
    @deprecated("default_authenticators", "3.0")
    def default_authenticator(self) -> Optional[Authenticator]:
        return self.default_authenticators[0] if self.default_authenticators else None

    def set_default_authenticator(self, authenticator: Authenticator) -> None:
        """
        Sets a handler authenticator to be used by default.

        :param Union(None, flask_rebar.authenticators.Authenticator) authenticator:
        """
        self.default_authenticators = (
            [authenticator] if authenticator is not None else []
        )

    def set_default_authenticators(self, authenticators: List[Authenticator]) -> None:
        """
        Sets the handler authenticators to be used by default.

        :param Union(List(flask_rebar.authenticators.Authenticator)) authenticators:
        """
        self.default_authenticators = authenticators or []

    def set_default_headers_schema(self, headers_schema: Schema) -> None:
        """
        Sets the schema to be used by default to validate incoming headers.

        :param marshmallow.Schema headers_schema:
        """
        self.default_headers_schema = normalize_schema(headers_schema)

    def clone(self) -> HandlerRegistry:
        """
        Returns a new, shallow-copied instance of :class:`HandlerRegistry`.

        :rtype: HandlerRegistry
        """
        return copy(self)

    def _prefixed(self, path: str) -> str:
        if self.prefix:
            return prefix_url(prefix=self.prefix, url=path)
        else:
            return path

    def _prefixed_spec_path(self) -> str:
        return self._prefixed(self.spec_path)

    def _prefixed_spec_ui_path(self) -> str:
        return self._prefixed(self.spec_ui_path)

    @property
    def paths(self) -> Dict[str, Dict[str, PathDefinition]]:
        # We duplicate the paths so we can modify the path definitions right before
        # they are accessed.
        paths: Dict[str, Dict[str, PathDefinition]] = defaultdict(dict)

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
                    response_body_schema=definition_.response_body_schema,
                    query_string_schema=definition_.query_string_schema,
                    request_body_schema=definition_.request_body_schema,
                    headers_schema=definition_.headers_schema,
                    authenticators=definition_.authenticators,
                    tags=definition_.tags,
                    mimetype=definition_.mimetype,
                    hidden=definition_.hidden,
                    summary=definition_.summary,
                )

        return paths

    @deprecated_parameters(
        authenticator=(
            "authenticators",
            "3.0",
            _convert_authenticator_to_authenticators,
        )
    )
    def add_handler(
        self,
        func: Callable,
        rule: str,
        method: str = "GET",
        endpoint: Optional[str] = None,
        response_body_schema: Optional[Dict[int, Schema]] = None,
        query_string_schema: Optional[Schema] = None,
        request_body_schema: Optional[Schema] = None,
        headers_schema: Union[Type[USE_DEFAULT], Schema] = USE_DEFAULT,
        authenticators: Union[
            Type[USE_DEFAULT], List[Authenticator], Authenticator
        ] = USE_DEFAULT,
        tags: Optional[Sequence[str]] = None,
        mimetype: Union[Type[USE_DEFAULT], str] = USE_DEFAULT,
        hidden: bool = False,
        summary: Optional[str] = None,
    ) -> None:
        """
        Registers a function as a request handler.

        :param func:
            The Flask "view_func"
        :param str rule:
            The Flask "rule"
        :param str method:
            The HTTP method this handler accepts
        :param str endpoint:
        :param dict[int, marshmallow.Schema] response_body_schema:
            Dictionary mapping response codes to schemas to use to marshal
            the response. For now this assumes everything is JSON.
        :param marshmallow.Schema query_string_schema:
            Schema to use to deserialize query string arguments.
        :param marshmallow.Schema request_body_schema:
            Schema to use to deserialize the request body. For now this
            assumes everything is JSON.
        :param Type[USE_DEFAULT]|None|marshmallow.Schema headers_schema:
            Schema to use to grab and validate headers.
        :param Type[USE_DEFAULT]|None|List(Authenticator)|Authenticator authenticators:
            A list of authenticator objects to authenticate incoming requests.
            If left as USE_DEFAULT, the Rebar's default will be used.
            Set to None to make this an unauthenticated handler.
        :param Sequence[str] tags:
            Arbitrary strings to tag the handler with. These will translate to Swagger operation tags.
        :param Type[USE_DEFAULT]|None|str mimetype:
            Content-Type header to add to the response schema
        :param bool hidden:
            if hidden, documentation is not created for this request handler by default
        :param str summary:
        """
        # Fix #115: if we were passed bare classes we'll go ahead and instantiate
        headers_schema = normalize_schema(headers_schema)
        request_body_schema = normalize_schema(request_body_schema)
        query_string_schema = normalize_schema(query_string_schema)
        if response_body_schema:
            # Ensure we wrap in appropriate default (200) dict if we were passed a single Schema or class:
            if not isinstance(response_body_schema, Mapping):
                response_body_schema = {200: response_body_schema}
            # use normalize_schema to convert any class reference(s) to instantiated schema(s):
            response_body_schema = {
                code: normalize_schema(schema)
                for (code, schema) in response_body_schema.items()
            }

        # authenticators can be a list of Authenticators, a single Authenticator, USE_DEFAULT, or None
        authenticators_list: Sequence[Union[Type[USE_DEFAULT], Authenticator]] = []
        if isinstance(authenticators, list):
            authenticators_list = authenticators
        elif isinstance(authenticators, Authenticator) or authenticators is USE_DEFAULT:
            authenticators_list = [authenticators]
        elif authenticators is None:
            authenticators_list = []

        self._paths[rule][method] = PathDefinition(
            func=func,
            path=rule,
            method=method,
            endpoint=endpoint,
            response_body_schema=response_body_schema,
            query_string_schema=query_string_schema,
            request_body_schema=request_body_schema,
            headers_schema=headers_schema,
            authenticators=authenticators_list,
            tags=tags,
            mimetype=mimetype,
            hidden=hidden,
            summary=summary,
        )

    @deprecated_parameters(
        authenticator=(
            "authenticators",
            "3.0",
            _convert_authenticator_to_authenticators,
        )
    )
    def handles(
        self,
        rule: str,
        method: str = "GET",
        endpoint: Optional[str] = None,
        response_body_schema: Optional[Dict[int, Schema]] = None,
        query_string_schema: Optional[Schema] = None,
        request_body_schema: Optional[Schema] = None,
        headers_schema: Union[Type[USE_DEFAULT], Schema] = USE_DEFAULT,
        authenticators: Union[
            Type[USE_DEFAULT], List[Authenticator], Authenticator
        ] = USE_DEFAULT,
        tags: Optional[Sequence[str]] = None,
        mimetype: Union[Type[USE_DEFAULT], str] = USE_DEFAULT,
        hidden: bool = False,
        summary: Optional[str] = None,
    ) -> Callable:
        """
        Same arguments as :meth:`HandlerRegistry.add_handler`, except this can
        be used as a decorator.
        """

        def wrapper(f: Callable[P, T]) -> Callable[P, T]:
            self.add_handler(
                func=f,
                rule=rule,
                method=method,
                endpoint=endpoint,
                response_body_schema=response_body_schema,
                query_string_schema=query_string_schema,
                request_body_schema=request_body_schema,
                headers_schema=headers_schema,
                authenticators=authenticators,
                tags=tags,
                mimetype=mimetype,
                hidden=hidden,
                summary=summary,
            )
            return f

        return wrapper

    def register(self, app: Flask) -> None:
        self._register_routes(app=app)
        self._register_swagger(app=app)
        self._register_swagger_ui(app=app)

    def _register_routes(self, app: Flask) -> None:
        for handler in self.handlers:
            for handler_mod in find_modules(import_path=handler, recursive=True):
                import_string(handler_mod)

        for path, methods in self.paths.items():
            for method, definition_ in methods.items():
                if definition_.endpoint:
                    endpoint = definition_.endpoint
                else:
                    endpoint = definition_.func.__name__

                if self.prefix:
                    endpoint = ".".join((self.prefix, endpoint))

                authenticators = []
                for authenticator in definition_.authenticators:
                    if authenticator is USE_DEFAULT:
                        authenticators.extend(self.default_authenticators)
                    else:
                        authenticators.append(authenticator)

                app.add_url_rule(
                    rule=definition_.path,
                    view_func=_wrap_handler(
                        f=definition_.func,
                        authenticators=authenticators,
                        query_string_schema=definition_.query_string_schema,
                        request_body_schema=definition_.request_body_schema,
                        headers_schema=(
                            self.default_headers_schema
                            if definition_.headers_schema is USE_DEFAULT
                            else definition_.headers_schema
                        ),
                        response_body_schema=definition_.response_body_schema,
                        mimetype=(
                            self.default_mimetype
                            if definition_.mimetype is USE_DEFAULT
                            else definition_.mimetype
                        ),
                    ),
                    methods=[definition_.method],
                    endpoint=endpoint,
                )

    def _register_swagger(self, app: Flask) -> None:
        swagger_endpoint = "get_swagger"

        if self.prefix:
            swagger_endpoint = ".".join((self.prefix, swagger_endpoint))

        if self.spec_path:

            @app.route(
                self._prefixed_spec_path(), methods=["GET"], endpoint=swagger_endpoint
            )
            def get_swagger() -> Response:
                swagger = self.swagger_generator.generate_swagger(
                    registry=self, host=request.host_url.rstrip("/")
                )
                return response(data=swagger)

    def _register_swagger_ui(self, app: Flask) -> None:
        blueprint_name = "swagger_ui"

        if self.prefix:
            blueprint_name = self.prefix.replace(".", "_") + blueprint_name

        if self.spec_ui_path:
            blueprint = create_swagger_ui_blueprint(
                name=blueprint_name,
                ui_url=self._prefixed_spec_ui_path(),
                swagger_url=self._prefixed_spec_path(),
            )
            app.register_blueprint(
                blueprint=blueprint, url_prefix=self._prefixed_spec_ui_path()
            )


class Rebar:
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

    def __init__(self) -> None:
        self.handler_registries: Set[HandlerRegistry] = set()
        self.paths: Dict[str, Dict[str, PathDefinition]] = defaultdict(dict)
        self.uncaught_exception_handlers: List[Callable] = []
        # If a developer doesn't wish to advertise that they are using rebar this can be used to control
        # the name of the attribute in error responses, or set to None to suppress inclusion of error codes entirely
        self.error_code_attr = "rebar_error_code"
        self.validate_on_dump = False

    @deprecated_parameters(
        default_authenticator=(
            "default_authenticators",
            "3.0",
            _convert_authenticator_to_authenticators,
        )
    )
    def create_handler_registry(
        self,
        prefix: Optional[str] = None,
        default_authenticators: Union[List[Authenticator], Authenticator, None] = None,
        default_headers_schema: Optional[Schema] = None,
        default_mimetype: Optional[str] = None,
        swagger_generator: Optional[SwaggerGenerator] = None,
        spec_path: str = "/swagger",
        swagger_ui_path: str = "/swagger/ui",
        handlers: Optional[List[str]] = None,
    ) -> HandlerRegistry:
        """
        Create a new handler registry and add to this extension's set of
        registered registries.

        When calling :meth:`Rebar.init_app`, all registries created via this method
        will be registered with the Flask application.

        Parameters are the same for the :class:`HandlerRegistry` constructor.

        :param str prefix:
            URL prefix for all handlers registered with this registry instance.
        :param Union(List(Authenticator), Authenticator, None) default_authenticators:
            List of Authenticators to use for all handlers as a default.
        :param marshmallow.Schema default_headers_schema:
            Schema to validate the headers on all requests as a default.
        :param str default_mimetype:
            Default response content-type if no content and not otherwise specified by the handler.
        :param flask_rebar.swagger_generation.swagger_generator.SwaggerGeneratorI swagger_generator:
            Object to generate a Swagger specification from this registry. This will be
            the Swagger generator that is used in the endpoints swagger and swagger UI
            that are added to the API.
            If left as None, a `SwaggerV2Generator` instance will be used.
        :param str spec_path:
            The OpenAPI specification as a JSON document will be hosted at this URL.
            If set as None, no swagger specification will be hosted.
        :param str swagger_ui_path:
            The HTML Swagger UI will be hosted at this URL.
            If set as None, no Swagger UI will be hosted.
        :param list handlers: directories where handlers should be imported from.
        :rtype: HandlerRegistry
        """
        registry = HandlerRegistry(
            prefix=prefix,
            default_authenticators=default_authenticators,
            default_headers_schema=default_headers_schema,
            default_mimetype=default_mimetype,
            swagger_generator=swagger_generator,
            spec_path=spec_path,
            spec_ui_path=swagger_ui_path,
            handlers=handlers,
        )
        self.add_handler_registry(registry=registry)
        return registry

    def add_handler_registry(self, registry: HandlerRegistry) -> None:
        """
        Register a handler registry with the extension.

        There is no need to call this if a handler registry was created
        via :meth:`Rebar.create_handler_registry`.

        :param HandlerRegistry registry:
        """
        self.handler_registries.add(registry)

    @property
    def validated_body(self) -> Dict[str, Any]:
        """
        Proxy to the result of validating/transforming an incoming request body with
        the `request_body_schema` a handler was registered with.

        :rtype: dict
        """
        return get_validated_body()

    @property
    def validated_args(self) -> Dict[str, Any]:
        """
        Proxy to the result of validating/transforming an incoming request's query
        string with the `query_string_schema` a handler was registered with.

        :rtype: dict
        """
        return get_validated_args()

    @property
    def validated_headers(self) -> Dict[str, str]:
        """
        Proxy to the result of validating/transforming an incoming request's headers
        with the `headers_schema` a handler was registered with.

        :rtype: dict
        """
        return get_validated_headers()

    def add_uncaught_exception_handler(self, func: Callable) -> None:
        """
        Add a function that will be called for uncaught exceptions, i.e. exceptions
        that will result in a 500 error.

        This function should accept the exception instance as a single positional argument.

        All handlers will be called in the order they are added.

        :param Callable func:
        """
        self.uncaught_exception_handlers.append(func)

    def init_app(self, app: Flask) -> None:
        """
        Register all the handler registries with a Flask application.

        :param flask.Flask app:
        """
        self._init_error_handling(app=app)

        for registry in self.handler_registries:
            registry.register(app=app)

        app.extensions["rebar"] = {
            "instance": self,
            "handler_registries": self.handler_registries,
        }

    def _init_error_handling(self, app: Flask) -> None:
        @app.errorhandler(errors.HttpJsonError)
        def handle_http_error(error: HttpJsonError) -> Response:
            return self._create_json_error_response(
                message=error.error_message,
                http_status_code=error.http_status_code,
                additional_data=error.additional_data,
            )

        @app.errorhandler(400)
        @app.errorhandler(404)
        @app.errorhandler(405)
        def handle_werkzeug_http_error(error: HTTPException) -> Response:
            return self._create_json_error_response(
                message=error.description, http_status_code=error.code
            )

        @app.errorhandler(MOVED_PERMANENTLY_ERROR)
        @app.errorhandler(PERMANENT_REDIRECT_ERROR)
        def handle_request_redirect_error(error: RequestRedirect) -> Response:
            return self._create_json_error_response(
                message=error.name,
                http_status_code=error.code,
                additional_data={"new_url": error.new_url},
                headers={"Location": error.new_url},
            )

        def run_unhandled_exception_handlers(exception: BaseException) -> None:
            exc_info = sys.exc_info()
            current_app.log_exception(exc_info=exc_info)

            for func in self.uncaught_exception_handlers:
                func(exception)

        @app.errorhandler(Exception)
        def handle_generic_error(error: Exception) -> Response:
            run_unhandled_exception_handlers(error)

            if current_app.debug:
                raise error
            else:
                return self._create_json_error_response(
                    message=messages.internal_server_error, http_status_code=500
                )

        @app.teardown_request
        def teardown(exception: Optional[BaseException]) -> None:
            if isinstance(exception, SystemExit):
                try:
                    run_unhandled_exception_handlers(exception)
                except Exception:
                    # make sure the exception handlers dont prevent teardown
                    pass

    def _create_json_error_response(
        self,
        message: Optional[Union[ErrorMessage, str]],
        http_status_code: Optional[int],
        additional_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """
        Compiles a response object for an error.

        :param Union[messages.ErrorMessage,str] message:
        :param int http_status_code:
          An optional, application-specific error code to add to the response.
        :param dict additional_data:
          Additional JSON data to attach to the response.
        :param dict headers:
          Additional headers to attach to the response.
        :rtype: flask.Response
        """
        if isinstance(message, messages.ErrorMessage):
            message_text = message.message
            rebar_error_code = message.rebar_error_code
        else:
            message_text = message
            rebar_error_code = None
        body = {"message": message_text}
        if additional_data:
            body.update(additional_data)
        if rebar_error_code and self.error_code_attr:
            body[self.error_code_attr] = rebar_error_code
        resp = jsonify(body)
        if headers:
            for key, value in headers.items():
                resp.headers[key] = value
        if http_status_code is not None:
            resp.status_code = http_status_code
        return resp
