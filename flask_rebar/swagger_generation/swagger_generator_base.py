"""
    Swagger Generator
    ~~~~~~~~~~~~~~~~~

    Base classes for swagger generators.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

import abc
import functools

from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.compat import ABC
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    authenticator_converter_registry as global_authenticator_converter_registry,
    make_class_from_method,
)
from flask_rebar.swagger_generation.marshmallow_to_swagger import (
    headers_converter_registry as global_headers_converter_registry,
)
from flask_rebar.swagger_generation.marshmallow_to_swagger import (
    query_string_converter_registry as global_query_string_converter_registry,
)
from flask_rebar.swagger_generation.marshmallow_to_swagger import (
    request_body_converter_registry as global_request_body_converter_registry,
)
from flask_rebar.swagger_generation.marshmallow_to_swagger import (
    response_converter_registry as global_response_converter_registry,
)
from flask_rebar.validation import Error
from flask_rebar.utils.deprecation import deprecated


class SwaggerGeneratorI(ABC):
    @abc.abstractmethod
    def get_open_api_version(self):
        """
        Rebar supports multiple OpenAPI specifications.
        :return: The OpenAPI specification the generator supports.
        """

    @abc.abstractmethod
    def generate_swagger(self, registry, host=None):
        """
        Generate a swagger definition json object.
        :param registry:
        :param host:
        :return:
        """

    @abc.abstractmethod
    def register_flask_converter_to_swagger_type(self, flask_converter, swagger_type):
        """
        Flask has "converters" that convert path arguments to a Python type.

        We need to map these to Swagger types. This allows additional flask
        converter types (they're pluggable!) to be mapped to Swagger types.

        Unknown Flask converters will default to string.

        :param str flask_converter:
        :param str swagger_type:
        """

    @abc.abstractmethod
    def register_authenticator_converter(self, authenticator_class, converter):
        """
        The Rebar allows for custom Authenticators.

        If you have a custom Authenticator, you need to add a function that
        can convert that authenticator to a Swagger representation.

        That function should take a single positional argument, which is the
        authenticator instance to be converted, and it should return a tuple
        where the first item is a name to use for the Swagger security
        definition, and the second item is the definition itself.

        :param Type[Authenticator] authenticator_class:
        :param function converter:
        """


class SwaggerGenerator(SwaggerGeneratorI):
    """Base class for SwaggerV2Generator and SwaggerV3Generator.

    Inheritance is a fragile way to share code, but its a convenient one...

    :param int openapi_major_version: Major version of the Swagger specification this will produce
    :param str version: Version of the API this swagger is specifying
    :param str title: Title of the API this swagger is specifying
    :param str description: Descrption of the API this swagger is specifying

    :param ConverterRegistry query_string_converter_registry:
    :param ConverterRegistry request_body_converter_registry:
    :param ConverterRegistry headers_converter_registry:
    :param ConverterRegistry response_converter_registry:
        ConverterRegistry instances that will be used to convert Marshmallow schemas
        to the corresponding types of swagger objects. These default to the
        global registries.

    :param marshmallow.Schema default_response_schema: Schema to use as the default of all responses
    """

    _open_api_version = None

    def __init__(
        self,
        openapi_major_version,
        version="1.0.0",
        title="My API",
        description="",
        query_string_converter_registry=None,
        request_body_converter_registry=None,
        headers_converter_registry=None,
        response_converter_registry=None,
        default_response_schema=Error(),
        authenticator_converter_registry=None,
    ):
        self.title = title
        self.version = version
        self.description = description
        self._query_string_converter = self._create_converter(
            query_string_converter_registry,
            global_query_string_converter_registry,
            openapi_major_version,
        )
        self._request_body_converter = self._create_converter(
            request_body_converter_registry,
            global_request_body_converter_registry,
            openapi_major_version,
        )
        self._headers_converter = self._create_converter(
            headers_converter_registry,
            global_headers_converter_registry,
            openapi_major_version,
        )
        self._response_converter = self._create_converter(
            response_converter_registry,
            global_response_converter_registry,
            openapi_major_version,
        )

        self.flask_converters_to_swagger_types = {
            "uuid": sw.string,
            "uuid_string": sw.string,
            "string": sw.string,
            "path": sw.string,
            "int": sw.integer,
            "float": sw.number,
        }

        self.authenticator_converter = self._create_authenticator_converter(
            authenticator_converter_registry,
            global_authenticator_converter_registry,
            openapi_major_version,
        )

        self.default_response_schema = default_response_schema

    def _get_info(self):
        return {
            sw.version: self.version,
            sw.title: self.title,
            sw.description: self.description,
        }

    def _create_converter(
        self, converter_registry, default_registry, openapi_major_version
    ):
        return functools.partial(
            (converter_registry or default_registry).convert,
            openapi_version=openapi_major_version,
        )

    def _create_authenticator_converter(
        self, converter_registry, default_registry, openapi_major_version
    ):
        registry = type("authenticator_converter_registry", (), {})
        registry.get_security_schemes = functools.partial(
            (converter_registry or default_registry).get_security_schemes,
            openapi_version=openapi_major_version,
        )
        registry.get_security_requirements = functools.partial(
            (converter_registry or default_registry).get_security_requirements,
            openapi_version=openapi_major_version,
        )
        registry.register_type = functools.partial(
            (converter_registry or default_registry).register_type,
        )

        return registry

    def get_open_api_version(self):
        return self._open_api_version

    def register_flask_converter_to_swagger_type(self, flask_converter, swagger_type):
        self.flask_converters_to_swagger_types[flask_converter] = swagger_type

    @deprecated(eol_version="2.0")
    def register_authenticator_converter(self, authenticator_class, converter):
        converter_class = make_class_from_method(authenticator_class, converter)
        self.authenticator_converter.register_type(converter_class())
