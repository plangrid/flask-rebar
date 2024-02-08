from collections import namedtuple
from typing import Type

from flask_rebar.authenticators import Authenticator, HeaderApiKeyAuthenticator
from .marshmallow_to_swagger import UnregisteredType
from . import swagger_words as sw
from typing import Any, Callable, Dict, Iterable, List, Optional


_Context = namedtuple(
    "_Context",
    [
        # The major version of OpenAPI being converter for
        "openapi_version"
    ],
)


class AuthenticatorConverter:
    """
    Abstract class for objects that convert Authenticator objects to
    security JSONSchema.

    When implementing your own AuthenticatorConverter you will need to:

    1) Set AUTHENTICATOR_TYPE to be your custom Authenticator class.

    2) Configure get_security_scheme to return a map of Security Scheme Objects.
        You should check for the openapi_version in context.openapi_version;
        If generation is requested for a version of the OpenAPI specification
        you do not intend to support,  we recommend raising a NotImplementedError.

    3) Configure get_security_requirements to return a list of Security Requirement Objects.
        You should check for the openapi_version in context.openapi_version;
        If generation is requested for a version of the OpenAPI specification
        you do not intend to support, we recommend raising a NotImplementedError.

    """

    AUTHENTICATOR_TYPE: Type[Authenticator]

    def get_security_schemes(
        self, obj: Authenticator, context: Optional[_Context] = None
    ) -> Dict[str, Any]:
        """
        Get the security schemes for the provided Authenticator object.

        OpenAPI Specification for defining security schemes
        2.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#security-definitions-object
        3.1.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md#fixed-fields-6
                (see securitySchemes field)

        OpenAPI Specification for Security Scheme Object
        2.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#security-scheme-object
        3.1.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md#security-scheme-object


        Example: An authenticator that makes use of an api_key and an application_key scheme
        {
            "api_key": {
                "type: "apiKey",
                "in": "header",
                "name": "X-API-Key"
            },
            "application_key" : {
                "type": "apiKey",
                "in": "query",
                "name": "application-key"
            }
        }

        Note: It is fine for multiple Authenticators to share Security Scheme definitions. Each Authenticator should
                return all scheme definitions that it makes use of.

        :param flask.authenticators.Authenticator obj: Authenticator instance to generate swagger for.
                    You can assume this is of type AUTHENTICATOR_TYPE
        :param _Context context: The context swagger is being generated for.
        :rtype: dict: Key should be the name for the scheme, the value should be a Security Scheme Object
        """
        raise NotImplementedError()

    def get_security_requirements(
        self, obj: Authenticator, context: Optional[_Context] = None
    ) -> List[Any]:
        """
        Get the security requirements for the provided Authenticator object

        OpenAPI Specification for Security Requirement Object
        2.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#security-requirement-object
        3.1.0: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.1.0.md#security-requirement-object

        Example: Require oauth with scope "read:stuff" OR api_key AND application_key
        [
            {"oauth": ["read:stuff"] },
            {"api_key": [], "application_key": []}
        ]

        :param flask_rebar.authenticators.Authenticator obj:
        :param _Context context:
        :rtype: list
        """
        raise NotImplementedError()


def make_class_from_method(
    authenticator_class: Type[Authenticator], func: Callable
) -> Type[AuthenticatorConverter]:
    """
    Utility to handle converting old-style method converters into new-style AuthenticatorConverters.
    """
    name = authenticator_class.__name__ + "Converter"
    meta = {
        "AUTHENTICATOR_TYPE": authenticator_class,
        "get_security_schemes": lambda self, obj, context: dict([func(obj)]),
        "get_security_requirements": lambda self, obj, context: [{func(obj)[0]: []}],
    }
    return type(name, (AuthenticatorConverter,), meta)


class HeaderApiKeyConverter(AuthenticatorConverter):
    AUTHENTICATOR_TYPE = HeaderApiKeyAuthenticator

    def get_security_requirements(
        self, obj: Authenticator, context: Optional[_Context] = None
    ) -> List[Dict[str, List]]:
        """
        :param HeaderApiKeyAuthenticator obj:
        :param _Context context:
        :return: list
        """
        if not isinstance(obj, HeaderApiKeyAuthenticator):
            raise NotImplementedError("Only HeaderApiKeyAuthenticator is supported")
        return [{obj.name: []}]

    def get_security_schemes(
        self, obj: Authenticator, context: Optional[_Context] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        :param HeaderApiKeyAuthenticator obj:
        :param _Context context:
        :return: dict
        """
        if not isinstance(obj, HeaderApiKeyAuthenticator):
            raise NotImplementedError("Only HeaderApiKeyAuthenticator is supported")
        return {
            obj.name: {sw.type_: sw.api_key, sw.in_: sw.header, sw.name: obj.header}
        }


class AuthenticatorConverterRegistry:
    def __init__(self) -> None:
        self._type_map: Dict[Type[Authenticator], AuthenticatorConverter] = {}

    def _convert(self, obj: Authenticator, context: _Context) -> None:
        pass

    def convert(self, obj: Authenticator, openapi_version: int = 2) -> Dict[str, Any]:
        raise RuntimeWarning("Use get_security_schemes or get_security_requirements")

    def register_type(self, converter: AuthenticatorConverter) -> None:
        """
        Registers a converter.

        :param AuthenticatorConverter converter:
        """
        self._type_map[converter.AUTHENTICATOR_TYPE] = converter

    def register_types(self, converters: Iterable[AuthenticatorConverter]) -> None:
        """
        Registers multiple converters.

        :param iterable[AuthenticatorConverter] converters:
        """
        for converter in converters:
            self.register_type(converter)

    def _get_converter_for_type(self, obj: Authenticator) -> AuthenticatorConverter:
        """
        Locates the registered converter for a given type.
        :param obj: instance to convert
        :return: converter for type of instance
        """
        method_resolution_order = obj.__class__.__mro__

        for cls in method_resolution_order:
            if cls in self._type_map:
                return self._type_map[cls]
        else:
            raise UnregisteredType(
                "No registered type found in method resolution order: {mro}\n"
                "Registered types: {types}".format(
                    mro=method_resolution_order, types=list(self._type_map.keys())
                )
            )

    def get_security_schemes(
        self, authenticator: Authenticator, openapi_version: int = 2
    ) -> Dict[str, Any]:
        """
        Get the security schemes for the provided Authenticator object

        :param flask.authenticators.Authenticator obj:
        :param int openapi_version: major version of OpenAPI to convert obj for
        :rtype: dict
        """
        # Remove this once legacy is gone
        if not isinstance(authenticator, Authenticator):
            return self.get_security_schemes_legacy(registry=authenticator)
        return self._get_converter_for_type(authenticator).get_security_schemes(
            authenticator, _Context(openapi_version=openapi_version)
        )

    def get_security_requirements(
        self, authenticator: Authenticator, openapi_version: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get the security requirements for the provided Authenticator object

        :param flask_rebar.authenticators.Authenticator obj:
        :param int openapi_version: major version of OpenAPI to convert obj for
        :rtype: list
        """
        return self._get_converter_for_type(authenticator).get_security_requirements(
            authenticator, _Context(openapi_version=openapi_version)
        )


authenticator_converter_registry = AuthenticatorConverterRegistry()
authenticator_converter_registry.register_types((HeaderApiKeyConverter(),))
