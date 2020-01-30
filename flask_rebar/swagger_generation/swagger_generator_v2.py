"""
    Swagger V2 Generator
    ~~~~~~~~~~~~~~~~~~~~

    Class for converting a handler registry into a Swagger V2 specification.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals

import copy

from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.authenticators import USE_DEFAULT
from flask_rebar.swagger_generation.generator_utils import (
    format_path_for_swagger,
    verify_parameters_are_the_same,
    get_response_description,
    create_ref,
    recursively_convert_dict_to_ordered_dict,
    get_unique_schema_definitions,
    get_ref_schema,
    get_unique_authenticators,
)
from flask_rebar.swagger_generation.marshmallow_to_swagger import get_swagger_title
from flask_rebar.validation import Error
from flask_rebar.swagger_generation.swagger_generator import SwaggerGenerator


class SwaggerV2Generator(SwaggerGenerator):
    """
    Generates a v2.0 Swagger specification from a Rebar object.

    Not all things are retrievable from the Rebar object, so this
    guy also needs some additional information to complete the job.

    :param str host:
        Host name or ip of the API. This is not that useful for generating a
        static specification that will be used across multiple hosts (i.e.
        PlanGrid folks, don't worry about this guy. We have to override it
        manually when initializing a client anyways.
    :param Sequence[str] schemes: "http", "https", "ws", or "wss".
        Defaults to empty. If left empty, the Swagger UI will infer the scheme
        from the document URL, ensuring that the "Try it out" buttons work.
    :param Sequence[str] consumes: Mime Types the API accepts
    :param Sequence[str] produces: Mime Types the API returns

    :param ConverterRegistry query_string_converter_registry:
    :param ConverterRegistry request_body_converter_registry:
    :param ConverterRegistry headers_converter_registry:
    :param ConverterRegistry response_converter_registry:
        ConverterRegistrys that will be used to convert Marshmallow schemas
        to the corresponding types of swagger objects. These default to the
        global registries.

    :param Sequence[Tag] tags:
        A list of tags used by the specification with additional metadata. \
    """

    _open_api_version = "2.0"

    def __init__(
        self,
        host="localhost",
        schemes=(),
        consumes=("application/json",),
        produces=("application/json",),
        version="1.0.0",
        title="My API",
        description="",
        query_string_converter_registry=None,
        request_body_converter_registry=None,
        headers_converter_registry=None,
        response_converter_registry=None,
        tags=None,
        default_response_schema=Error(),
        authenticator_converter_registry=None,
    ):
        super(SwaggerV2Generator, self).__init__(
            openapi_major_version=2,
            version=version,
            title=title,
            description=description,
            default_response_schema=default_response_schema,
            query_string_converter_registry=query_string_converter_registry,
            request_body_converter_registry=request_body_converter_registry,
            headers_converter_registry=headers_converter_registry,
            response_converter_registry=response_converter_registry,
            authenticator_converter_registry=authenticator_converter_registry,
        )
        self.host = host
        self.schemes = schemes
        self.consumes = consumes
        self.produces = produces
        self.tags = tags
        self._ref_base = "#/definitions"

    def generate_swagger(self, registry, host=None):
        return self.generate(registry=registry, host=host)

    def generate(
        self,
        registry,
        host=None,
        schemes=None,
        consumes=None,
        produces=None,
        sort_keys=True,
    ):
        """Generate a swagger specification from the provided `registry`

        `generate_swagger` implements the SwaggerGeneratorI interface. But for backwards compatibility,
        we are keeping the similarly named `generate` signature.

        :param flask_rebar.rebar.HandlerRegistry registry:
        :param str host: Overrides the initialized host
        :param Sequence[str] schemes: Overrides the initialized schemas
        :param Sequence[str] consumes: Overrides the initialized consumes
        :param Sequence[str] produces: Overrides the initialized produces
        :param bool sort_keys: Use OrderedDicts sorted by keys instead of dicts
        :rtype: dict
        """

        security_definitions = {}
        authenticators = get_unique_authenticators(registry)
        for authenticator in authenticators:
            # We should probably eventually check that scheme with the same name are identical
            # rather than just overwriting the existing scheme definition.
            security_definitions.update(
                self.authenticator_converter.get_security_schemes(authenticator)
            )

        default_security = []
        for authenticator in registry.default_authenticators:
            default_security.extend(
                self.authenticator_converter.get_security_requirements(authenticator)
            )

        definitions = get_unique_schema_definitions(
            registry=registry,
            base=self._ref_base,
            default_response_schema=self.default_response_schema,
            response_converter=self._response_converter,
            request_body_converter=self._request_body_converter,
        )
        paths = self._get_paths(
            paths=registry.paths,
            default_headers_schema=registry.default_headers_schema,
            default_security=default_security,
        )

        if host and "://" in host:
            _, _, host = host.partition("://")

        swagger = {
            sw.swagger: self.get_open_api_version(),
            sw.info: self._get_info(),
            sw.host: host or self.host,
            sw.schemes: list(schemes or self.schemes),
            sw.consumes: list(consumes or self.consumes),
            sw.produces: list(produces or self.produces),
            sw.security_definitions: security_definitions,
            sw.paths: paths,
            sw.definitions: definitions,
        }

        if default_security:
            swagger[sw.security] = default_security

        if self.tags:
            swagger[sw.tags] = [tag.as_swagger() for tag in self.tags]

        if sort_keys:
            # Sort the swagger we generated by keys to produce a consistent output.
            swagger = recursively_convert_dict_to_ordered_dict(swagger)

        return swagger

    def _get_paths(self, paths, default_headers_schema, default_security=None):
        path_definitions = {}

        for path, methods in paths.items():
            swagger_path, path_args = format_path_for_swagger(path)

            # Different Flask paths might correspond to the same Swagger path
            # because of Flask URL path converters. In this case, let's just
            # work off the same path definitions.
            if swagger_path in path_definitions:
                path_definition = path_definitions[swagger_path]
            else:
                path_definitions[swagger_path] = path_definition = {}

            if path_args:
                path_params = [
                    {
                        sw.name: path_arg.name,
                        sw.required: True,
                        sw.in_: sw.path,
                        sw.type_: self.flask_converters_to_swagger_types[path_arg.type],
                    }
                    for path_arg in path_args
                ]

                # We have to check for an ugly case here. If different Flask
                # paths that map to the same Swagger path use different URL
                # converters for the same parameter, we have a problem. Let's
                # just throw an error in this case.
                if sw.parameters in path_definition:
                    verify_parameters_are_the_same(
                        path_definition[sw.parameters], path_params
                    )

                path_definition[sw.parameters] = path_params

            for method, d in methods.items():
                responses_definition = {
                    sw.default: {
                        sw.description: get_response_description(
                            self.default_response_schema
                        ),
                        sw.schema: {
                            sw.ref: create_ref(
                                self._ref_base,
                                get_swagger_title(self.default_response_schema),
                            )
                        },
                    }
                }

                if d.response_body_schema:
                    for status_code, schema in d.response_body_schema.items():
                        if schema is not None:
                            response_definition = {
                                sw.description: get_response_description(schema),
                                sw.schema: get_ref_schema(self._ref_base, schema),
                            }

                            responses_definition[str(status_code)] = response_definition
                        else:
                            responses_definition[str(status_code)] = {
                                sw.description: "No response body."
                            }

                parameters_definition = []

                if d.query_string_schema:
                    parameters_definition.extend(
                        self._convert_jsonschema_to_list_of_parameters(
                            self._query_string_converter(d.query_string_schema),
                            in_=sw.query,
                        )
                    )

                if d.request_body_schema:
                    schema = d.request_body_schema

                    parameters_definition.append(
                        {
                            sw.name: schema.__class__.__name__,
                            sw.in_: sw.body,
                            sw.required: True,
                            sw.schema: get_ref_schema(self._ref_base, schema),
                        }
                    )

                if d.headers_schema is USE_DEFAULT and default_headers_schema:
                    parameters_definition.extend(
                        self._convert_jsonschema_to_list_of_parameters(
                            self._headers_converter(default_headers_schema),
                            in_=sw.header,
                        )
                    )
                elif (
                    d.headers_schema is not USE_DEFAULT and d.headers_schema is not None
                ):
                    parameters_definition.extend(
                        self._convert_jsonschema_to_list_of_parameters(
                            self._headers_converter(d.headers_schema), in_=sw.header
                        )
                    )

                method_lower = method.lower()
                path_definition[method_lower] = {
                    sw.operation_id: d.endpoint or get_swagger_title(d.func),
                    sw.responses: responses_definition,
                }

                if d.func.__doc__:
                    path_definition[method_lower][sw.description] = d.func.__doc__

                if parameters_definition:
                    path_definition[method_lower][sw.parameters] = parameters_definition

                if not d.authenticators:
                    path_definition[method_lower][sw.security] = []
                else:
                    non_default = False
                    security = []
                    for authenticator in d.authenticators:
                        if authenticator is not USE_DEFAULT:
                            security.extend(
                                self.authenticator_converter.get_security_requirements(
                                    authenticator
                                )
                            )
                            non_default = True
                        elif default_security is not None:
                            security.extend(default_security)
                    if non_default:
                        path_definition[method_lower][sw.security] = security

                if d.tags:
                    path_definition[method_lower][sw.tags] = d.tags

        return path_definitions

    def _convert_jsonschema_to_list_of_parameters(self, obj, in_="query"):
        """
        Swagger is only _based_ on JSONSchema. Query string and header parameters
        are represented as list, not as an object. This converts a JSONSchema
        object (as return by the converters) to a list of parameters suitable for
        swagger.

        :param dict obj:
        :param str in_: 'query' or 'header'
        :rtype: list[dict]
        """
        parameters = []

        assert obj["type"] == "object"

        required = obj.get("required", [])

        for name, prop in sorted(obj["properties"].items(), key=lambda i: i[0]):
            parameter = copy.deepcopy(prop)
            parameter["required"] = name in required
            parameter["in"] = in_
            parameter["name"] = name
            parameters.append(parameter)

        return parameters
