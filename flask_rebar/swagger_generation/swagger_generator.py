"""
    Swagger Generator
    ~~~~~~~~~~~~~~~~~

    Class for converting a handler registry into a Swagger specification.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from __future__ import unicode_literals

import copy
import re
from collections import namedtuple
from collections import OrderedDict

from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.authenticators import USE_DEFAULT
from flask_rebar.authenticators import HeaderApiKeyAuthenticator
from flask_rebar.swagger_generation.marshmallow_to_swagger import get_swagger_title
from flask_rebar.swagger_generation.marshmallow_to_swagger import headers_converter_registry as global_headers_converter_registry
from flask_rebar.swagger_generation.marshmallow_to_swagger import query_string_converter_registry as global_query_string_converter_registry
from flask_rebar.swagger_generation.marshmallow_to_swagger import request_body_converter_registry as global_request_body_converter_registry
from flask_rebar.swagger_generation.marshmallow_to_swagger import response_converter_registry as global_response_converter_registry
from flask_rebar.validation import Error


def _get_key(obj):
    """
    Returns the key for a JSONSchema object that we can use to make a $ref.

    We're just enforcing that objects all have a title for now.

    :param dict obj:
    :rtype: str
    """
    return obj[sw.title]


def _get_ref(key, path=('#', sw.definitions)):
    """
    Constructs a path for a JSONSchema $ref.

    #/definitions/MyObject
    '.__________.'._____.'
          |          |
        path        key

    :param str key:
    :param iterable[str] path:
    :rtype: str
    """
    return '/'.join(list(path) + [key])


def _get_response_description(schema):
    """
    Retrieves a response description from a Marshmallow schema.

    This is a required field, so we _have_ to give something back.

    :param marshmallow.Schema schema:
    :rtype: str
    """
    if schema.__doc__:
        return schema.__doc__
    else:
        return get_swagger_title(schema)


def _flatten(schema):
    """
    Recursively flattens a JSONSchema to a dictionary of keyed JSONSchemas,
    replacing nested objects with a reference to that object.


    Example input::
        {
          'type': 'object',
          'title': 'x',
          'properties': {
            'a': {
              'type': 'object',
              'title': 'y',
              'properties': {'b': {'type': 'integer'}}
            }
          }
        }

    Example output::
        {
          'x': {
            'type': 'object',
            'title': 'x',
            'properties': {
              'a': {'$ref': '#/definitions/y'}
            }
          },
          'y': {
            'type': 'object',
            'title': 'y',
            'properties': {'b': {'type': 'integer'}}
          }
        }

    This is useful for decomposing complex object generated from Marshmallow
    into a definitions object in Swagger.

    :param dict schema:
    :rtype: tuple(dict, dict)
    :returns: A tuple where the first item is the input object with any nested
    objects replaces with references, and the second item is the flattened
    definitions dictionary.
    """
    schema = copy.deepcopy(schema)

    definitions = {}

    if schema[sw.type_] == sw.object_:
        _flatten_object(schema=schema, definitions=definitions)
        schema = {sw.ref: _get_ref(_get_key(schema))}
    elif schema[sw.type_] == sw.array:
        _flatten_array(schema=schema, definitions=definitions)

    return schema, definitions


def _flatten_object(schema, definitions):
    if sw.title not in schema:
        # No need to flatten an object that doesn't have a title.
        # These are probably super simple objects that don't need
        # to be flattened.
        return

    for field, obj in schema[sw.properties].items():
        if obj[sw.type_] == sw.object_:
            obj_key = _flatten_object(schema=obj, definitions=definitions)
            if obj_key:
                schema[sw.properties][field] = {sw.ref: _get_ref(obj_key)}
        elif obj[sw.type_] == sw.array:
            _flatten_array(schema=obj, definitions=definitions)

    key = _get_key(schema)
    definitions[key] = schema

    return key


def _flatten_array(schema, definitions):
    if schema[sw.items][sw.type_] == sw.object_:
        obj_key = _flatten_object(schema=schema[sw.items], definitions=definitions)
        if obj_key:
            schema[sw.items] = {sw.ref: _get_ref(obj_key)}
    elif schema[sw.items][sw.type_] == sw.array:
        _flatten_array(schema=schema[sw.items], definitions=definitions)


def _convert_jsonschema_to_list_of_parameters(obj, in_='query'):
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

    assert obj['type'] == 'object'

    required = obj.get('required', [])

    for name, prop in obj['properties'].items():
        parameter = copy.deepcopy(prop)
        parameter['required'] = name in required
        parameter['in'] = in_
        parameter['name'] = name
        parameters.append(parameter)

    return parameters


_PATH_REGEX = re.compile('<((?P<type>.+?):)?(?P<name>.+?)>')
_PathArgument = namedtuple('PathArgument', ['name', 'type'])


def _format_path_for_swagger(path):
    """
    Flask and Swagger represent paths differently - this parses a Flask path
    to its Swagger form. This also extracts what the arguments in the flask
    path are, so we can represent them as parameters in Swagger.

    :param str path:
    :rtype: tuple(str, tuple(_PathArgument))
    """
    matches = list(_PATH_REGEX.finditer(path))

    args = tuple(
        _PathArgument(
            name=match.group('name'),
            type=match.group('type') or 'string'
        )
        for match in matches
    )

    subbed_path = _PATH_REGEX.sub(
        repl=lambda match: '{{{}}}'.format(match.group('name')),
        string=path
    )
    return subbed_path, args


def _convert_header_api_key_authenticator(authenticator):
    """
    Converts a HeaderApiKeyAuthenticator object to a Swagger definition.

    :param HeaderApiKeyAuthenticator authenticator:
    :rtype: tuple(str, dict)
    :returns: Tuple where the first item is a name for the authenticator, and
    the second item is a Swagger definition for it.
    """
    key = authenticator.name
    definition = {
        sw.name: authenticator.header,
        sw.in_: sw.header,
        sw.type_: sw.api_key
    }
    return key, definition


def _verify_parameters_are_the_same(a, b):
    def get_sort_key(parameter):
        return parameter[sw.name]

    sorted_a = sorted(a, key=get_sort_key)
    sorted_b = sorted(b, key=get_sort_key)

    if sorted_a != sorted_b:
        msg = (
            'Swagger generation does not support Flask url '
            'converters that map to different Swagger types!'
        )
        raise ValueError(msg)


class SwaggerV2Generator(object):
    """
    Generates a v2.0 Swagger specification from a Rebar object.

    Not all things are retrievable from the Rebar object, so this
    guy also needs some additional information to complete the job.

    :param str host:
        Host name or ip of the API. This is not that useful for generating a
        static specification that will be used across multiple hosts (i.e.
        PlanGrid folks, don't worry about this guy. We have to override it
        manually when initializing a client anyways.
    :param Sequence[str] schemes: "http", "https", "ws", or "wss"
    :param Sequence[str] consumes: Mime Types the API accepts
    :param Sequence[str] produces: Mime Types the API returns

    :param ConverterRegistry query_string_converter_registry:
    :param ConverterRegistry request_body_converter_registry:
    :param ConverterRegistry headers_converter_registry:
    :param ConverterRegistry response_converter_registry:
        ConverterRegistrys that will be used to convert Marshmallow schemas
        to the corresponding types of swagger objects. These default to the
        global registries.

    """
    def __init__(
            self,
            host='swag.com',
            schemes=('http',),
            consumes=('application/json',),
            produces=('application/vnd.plangrid+json',),
            version='1.0.0',
            title='My API',
            description='',
            query_string_converter_registry=None,
            request_body_converter_registry=None,
            headers_converter_registry=None,
            response_converter_registry=None,

            # TODO Still trying to figure out how to get this from the registry
            # Flask error handling doesn't mesh well with Swagger responses,
            # and I'm trying to avoid building our own layer on top of Flask's
            # error handlers.
            default_response_schema=Error()
    ):
        self.host = host
        self.schemes = schemes
        self.consumes = consumes
        self.produces = produces
        self.title = title
        self.description = description
        self.version = version

        self._query_string_converter = (
            query_string_converter_registry
            or global_query_string_converter_registry
        ).convert
        self._request_body_converter = (
            request_body_converter_registry
            or global_request_body_converter_registry
        ).convert
        self._headers_converter = (
            headers_converter_registry
            or global_headers_converter_registry
        ).convert
        self._response_converter = (
            response_converter_registry
            or global_response_converter_registry
        ).convert

        self.flask_converters_to_swagger_types = {
            'uuid': sw.string,
            'uuid_string': sw.string,
            'string': sw.string,
            'int': sw.integer,
            'float': sw.number
        }

        self.authenticator_converters = {
            HeaderApiKeyAuthenticator: _convert_header_api_key_authenticator
        }

        self.default_response_schema = default_response_schema

    def register_flask_converter_to_swagger_type(self, flask_converter, swagger_type):
        """
        Flask has "converters" that convert path arguments to a Python type.

        We need to map these to Swagger types. This allows additional flask
        converter types (they're pluggable!) to be mapped to Swagger types.

        Unknown Flask converters will default to string.

        :param str flask_converter:
        :param str swagger_type:
        """
        self.flask_converters_to_swagger_types[flask_converter] = swagger_type

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
        self.authenticator_converters[authenticator_class] = converter

    def generate(
            self,
            registry,
            host=None,
            schemes=None,
            consumes=None,
            produces=None
    ):
        """
        Generates a Swagger specification from a Rebar instance.

        :param flask_rebar.rebar.HandlerRegistry registry:
        :param str host: Overrides the initialized host
        :param Sequence[str] schemes: Overrides the initialized schemas
        :param Sequence[str] consumes: Overrides the initialized consumes
        :param Sequence[str] produces: Overrides the initialized produces
        :rtype: dict
        """
        default_authenticator = registry.default_authenticator
        security_definitions = self._get_security_definitions(
            paths=registry.paths,
            default_authenticator=default_authenticator
        )
        definitions = self._get_definitions(paths=registry.paths)
        paths = self._get_paths(
            paths=registry.paths,
            default_headers_schema=registry.default_headers_schema
        )

        swagger = {
            sw.swagger: self._get_version(),
            sw.info: self._get_info(),
            sw.host: host or self.host,
            sw.schemes: list(schemes or self.schemes),
            sw.consumes: list(consumes or self.consumes),
            sw.produces: list(produces or self.produces),
            sw.security_definitions: security_definitions,
            sw.paths: paths,
            sw.definitions: definitions
        }

        if default_authenticator:
            swagger[sw.security] = self._get_security(default_authenticator)

        # Sort the swagger we generated by keys to produce a consistent output.
        swagger = self._recursively_order_dicts(swagger)

        return swagger

    def _get_version(self):
        return '2.0'

    def _get_info(self):
        # TODO: add all the parameters for populating info
        return {
            sw.version: self.version,
            sw.title: self.title,
            sw.description: self.description,
        }

    def _get_security(self, authenticator):
        klass = authenticator.__class__
        converter = self.authenticator_converters[klass]
        name, _ = converter(authenticator)
        return [{name: []}]

    def _get_security_definitions(self, paths, default_authenticator):
        security_definitions = {}

        authenticators = set(
            d.authenticator
            for d in self._iterate_path_definitions(paths=paths)
            if d.authenticator is not None
            and d.authenticator is not USE_DEFAULT
        )

        if default_authenticator is not None:
            authenticators.add(default_authenticator)

        for authenticator in authenticators:
            klass = authenticator.__class__
            converter = self.authenticator_converters[klass]
            key, definition = converter(authenticator)
            security_definitions[key] = definition

        return security_definitions

    def _get_paths(self, paths, default_headers_schema):
        path_definitions = {}

        for path, methods in paths.items():
            swagger_path, path_args = _format_path_for_swagger(path)

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
                        sw.type_: self.flask_converters_to_swagger_types[path_arg.type]

                    }
                    for path_arg in path_args
                ]

                # We have to check for an ugly case here. If different Flask
                # paths that map to the same Swagger path use different URL
                # converters for the same parameter, we have a problem. Let's
                # just throw an error in this case.
                if sw.parameters in path_definition:
                    _verify_parameters_are_the_same(
                        path_definition[sw.parameters],
                        path_params
                    )

                path_definition[sw.parameters] = path_params

            for method, d in methods.items():
                responses_definition = {
                    sw.default: {
                        sw.description: _get_response_description(self.default_response_schema),
                        sw.schema: {
                            sw.ref: _get_ref(get_swagger_title(self.default_response_schema))
                        }
                    }
                }

                if d.marshal_schema:
                    for status_code, schema in d.marshal_schema.items():
                        if schema is not None:
                            response_definition = {
                                sw.description: _get_response_description(schema),
                                sw.schema: {sw.ref: _get_ref(get_swagger_title(schema))}
                            }

                            responses_definition[str(status_code)] = response_definition
                        else:
                            responses_definition[str(status_code)] = {
                                sw.description: 'No response body.'
                            }

                parameters_definition = []

                if d.query_string_schema:
                    parameters_definition.extend(
                        _convert_jsonschema_to_list_of_parameters(
                            self._query_string_converter(d.query_string_schema),
                            in_=sw.query
                        )
                    )

                if d.request_body_schema:
                    schema = d.request_body_schema

                    parameters_definition.append({
                        sw.name: schema.__class__.__name__,
                        sw.in_: sw.body,
                        sw.required: True,
                        sw.schema: {sw.ref: _get_ref(get_swagger_title(schema))}
                    })

                if d.headers_schema is USE_DEFAULT and default_headers_schema:
                    parameters_definition.extend(
                        _convert_jsonschema_to_list_of_parameters(
                            self._headers_converter(default_headers_schema),
                            in_=sw.header
                        )
                    )
                elif d.headers_schema is not USE_DEFAULT and d.headers_schema is not None:
                    parameters_definition.extend(
                        _convert_jsonschema_to_list_of_parameters(
                            self._headers_converter(d.headers_schema),
                            in_=sw.header
                        )
                    )

                method_lower = method.lower()
                path_definition[method_lower] = {
                    sw.operation_id: d.endpoint or get_swagger_title(d.func),
                    sw.responses: responses_definition
                }

                if d.func.__doc__:
                    path_definition[method_lower][sw.description] = d.func.__doc__

                if parameters_definition:
                    path_definition[method_lower][sw.parameters] = parameters_definition

                if d.authenticator is None:
                    path_definition[method_lower][sw.security] = []
                elif d.authenticator is not USE_DEFAULT:
                    security = self._get_security(d.authenticator)
                    path_definition[method_lower][sw.security] = security

        return path_definitions

    def _get_definitions(self, paths):
        all_schemas = set()

        converted = []

        all_schemas.add(self.default_response_schema)
        converted.append(self._response_converter(self.default_response_schema))

        for d in self._iterate_path_definitions(paths=paths):
            if d.marshal_schema:
                for schema in d.marshal_schema.values():
                    if schema is None:
                        # Responses that don't have a response body have None
                        # for a schema
                        continue

                    if schema not in all_schemas:
                        converted.append(self._response_converter(schema))
                    all_schemas.add(schema)

            if d.request_body_schema:
                schema = d.request_body_schema

                if schema not in all_schemas:
                    converted.append(self._request_body_converter(schema))

                all_schemas.add(schema)

        flattened = {}

        for obj in converted:
            _, flattened_definitions = _flatten(obj)
            flattened.update(flattened_definitions)

        return flattened

    def _iterate_path_definitions(self, paths):
        for methods in paths.values():
            for definition in methods.values():
                yield definition

    def _recursively_order_dicts(self, obj):
        if isinstance(obj, dict):
            sorted_dict = OrderedDict(sorted(obj.items(), key=lambda i: i[0]))
            for key, val in obj.items():
                sorted_dict[key] = self._recursively_order_dicts(val)
            return sorted_dict
        elif isinstance(obj, list):
            return [self._recursively_order_dicts(item) for item in obj]
        else:
            return obj
