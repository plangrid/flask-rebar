"""
    Swagger Generator
    ~~~~~~~~~~~~~~~~~

    Base classes for swagger generators.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

import abc
import functools
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from marshmallow import Schema

from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    authenticator_converter_registry as global_authenticator_converter_registry,
)
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    AuthenticatorConverter,
    AuthenticatorConverterRegistry,
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
from flask_rebar.swagger_generation.marshmallow_to_swagger import ConverterRegistry
from flask_rebar.validation import Error


# avoid circular imports
if TYPE_CHECKING:
    from flask_rebar.rebar import HandlerRegistry


class SwaggerGeneratorI(abc.ABC):
    @abc.abstractmethod
    def get_open_api_version(self) -> str:
        """
        Rebar supports multiple OpenAPI specifications.
        :return: The OpenAPI specification the generator supports.
        """

    @abc.abstractmethod
    def generate_swagger(
        self, registry: "HandlerRegistry", host: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a swagger definition json object.
        :param registry:
        :param host:
        :return:
        """

    @abc.abstractmethod
    def register_flask_converter_to_swagger_type(
        self, flask_converter: str, swagger_type: Any
    ) -> None:
        """
        Flask has "converters" that convert path arguments to a Python type.

        We need to map these to Swagger types. This allows additional flask
        converter types (they're pluggable!) to be mapped to Swagger types.

        Unknown Flask converters will default to string.

        :param str flask_converter:
        :param object swagger_type:
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

    _open_api_version: str

    def __init__(
        self,
        openapi_major_version: int,
        version: str = "1.0.0",
        title: str = "My API",
        description: str = "",
        query_string_converter_registry: Optional[ConverterRegistry] = None,
        request_body_converter_registry: Optional[ConverterRegistry] = None,
        headers_converter_registry: Optional[ConverterRegistry] = None,
        response_converter_registry: Optional[ConverterRegistry] = None,
        default_response_schema: Schema = Error(),
        authenticator_converter_registry: Optional[
            AuthenticatorConverterRegistry
        ] = None,
        include_hidden: bool = False,
    ):
        self.include_hidden = include_hidden
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

    def _get_info(self) -> Dict[str, str]:
        return {
            sw.version: self.version,
            sw.title: self.title,
            sw.description: self.description,
        }

    def _create_converter(
        self,
        converter_registry: Optional[ConverterRegistry],
        default_registry: ConverterRegistry,
        openapi_major_version: int,
    ) -> Callable:
        return functools.partial(
            (converter_registry or default_registry).convert,
            openapi_version=openapi_major_version,
        )

    def _create_authenticator_converter(
        self,
        converter_registry: Optional[AuthenticatorConverterRegistry],
        default_registry: AuthenticatorConverterRegistry,
        openapi_major_version: int,
    ) -> AuthenticatorConverter:
        registry: Any = type("authenticator_converter_registry", (), {})
        registry.get_security_schemes = functools.partial(
            (converter_registry or default_registry).get_security_schemes,
            openapi_version=openapi_major_version,
        )
        registry.get_security_requirements = functools.partial(
            (converter_registry or default_registry).get_security_requirements,
            openapi_version=openapi_major_version,
        )
        return registry

    def get_open_api_version(self) -> str:
        return self._open_api_version

    def register_flask_converter_to_swagger_type(
        self, flask_converter: str, swagger_type: Any
    ) -> None:
        """
        Register a converter for a type in flask to a swagger type.

        This can be used to alter the types of objects that already exist or add
        swagger types to objects that are added to the base flask configuration.

        For example, when adding custom path types to the Flask url_map, a
        converter can be added for customizing the swagger type.

        .. code-block:: python

            import enum

            from flask_rebar.swagger_generation import swagger_words as sw


            class TodoType(str, enum.Enum):
                user = "user"
                group = "group"


            class TodoTypeConverter:

                @staticmethod
                def to_swagger():
                    return {
                        sw.type_: sw.string,
                        sw.enum: [t.value for t in TodoType],
                    }

            @registry.handles(
                rule="/todos/<todo_type:type_>",
            )
            def get_todos_by_type(type_):
                ...

            generator.register_flask_converter_to_swagger_type(
                flask_converter="todo_type",
                swagger_type=TodoTypeConverter,
            )

        With the above example, when something is labeled as a ``todo_type`` in
        a path. The correct swagger can be returned.
        """
        self.flask_converters_to_swagger_types[flask_converter] = swagger_type
