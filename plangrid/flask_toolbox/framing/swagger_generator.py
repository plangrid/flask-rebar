from plangrid.flask_toolbox.framing import swagger_words as sw
import copy
import unittest

import marshmallow as m

import re
import json
from flask_testing import TestCase
from collections import defaultdict, namedtuple
from functools import wraps, reduce
from flask import Flask, Blueprint, request
from plangrid.flask_toolbox import get_query_string_params_or_400
from plangrid.flask_toolbox import get_json_body_params_or_400
from plangrid.flask_toolbox import marshal
from plangrid.flask_toolbox import response
from plangrid.flask_toolbox import Toolbox
from plangrid.flask_toolbox.validation import Error
from plangrid.flask_toolbox.framing.framer import HeaderApiKeyAuthenticator
from plangrid.flask_toolbox.framing import swagger_words as sw
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import query_string_converter_registry
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import request_body_converter_registry
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import headers_converter_registry
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import response_converter_registry
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import IN
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import OUT
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import get_schema_title
from plangrid.flask_toolbox.framing.marshmallow_to_jsonschema import convert_jsonschema_to_list_of_parameters


def _get_key(obj):
    return obj[sw.title]


def _get_ref(key, path=('#', sw.definitions,)):
    return '/'.join(list(path) + [key])


def _flatten_object(schema, definitions):
    for field, obj in schema[sw.properties].items():
        if obj[sw.type_] == sw.object_:
            obj_key = _flatten_object(schema=obj, definitions=definitions)
            schema[sw.properties][field] = {sw.ref: _get_ref(obj_key)}
        elif obj[sw.type_] == sw.array:
            _flatten_array(schema=obj, definitions=definitions)

    key = _get_key(schema)
    definitions[key] = schema

    return key


def _flatten_array(schema, definitions):
    if schema[sw.items][sw.type_] == sw.object_:
        obj_key = _flatten_object(schema=schema[sw.items], definitions=definitions)
        schema[sw.items] = {sw.ref: _get_ref(obj_key)}
    elif schema[sw.items][sw.type_] == sw.array:
        _flatten_array(schema=schema[sw.items], definitions=definitions)


# def _flatten_dfs(schema, definitions):
#     schema = copy.deepcopy(schema)
#
#     if schema[sw.type_] == sw.object_:
#         for field, obj in schema[sw.properties].items():
#             if obj[sw.type_] in (sw.object_, sw.array):
#                 obj_key = _flatten_dfs(schema=obj, definitions=definitions)
#                 schema[sw.properties][field] = {sw.ref: _get_ref(obj_key)}
#
#     if schema[sw.type_] == sw.array:
#         if schema[sw.items][sw.type_] in (sw.object_, sw.array):
#             obj_key = _flatten_dfs(schema=schema[sw.items], definitions=definitions)
#             schema[sw.items] = {sw.ref: _get_ref(obj_key)}
#
#     if schema[sw.type_] == sw.object_:
#         key = _get_key(schema)
#         definitions[key] = schema
#
#     return key


def _flatten(schema):
    schema = copy.deepcopy(schema)

    definitions = {}

    if schema[sw.type_] == sw.object_:
        _flatten_object(schema=schema, definitions=definitions)

        # TODO: cleaner way to do this? who cares?
        schema = {sw.ref: _get_ref(_get_key(schema))}
    elif schema[sw.type_] == sw.array:
        _flatten_array(schema=schema, definitions=definitions)

    return schema, definitions

_PATH_REGEX = re.compile('<((?P<type>.+?):)?(?P<name>.+?)>')


_PathArgument = namedtuple('PathArgument', ['name', 'type'])


def _sub(matchobj):
    return '{{{}}}'.format(matchobj.group('arg'))


def _format_path_for_swagger(path):
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

    :param HeaderApiKeyAuthenticator authenticator:
    :return:
    """
    key = authenticator.name
    definition = {
        sw.name: authenticator.header,
        sw.in_: sw.header,
        sw.type_: sw.api_key
    }
    return key, definition

class SwaggerV2Generator(object):
    def __init__(
            self,
            host='http://default.dev.planfront.net',
            schemes=('http',),
            consumes=('application/json',),
            produces=('application/vnd.plangrid+json',),
            mm_query_string_converter_registry=None,
            mm_request_body_converter_registry=None,
            mm_headers_converter_registry=None,
            mm_response_converter_registry=None,
            default_response_schema=Error()
    ):
        self.host = host
        self.schemes = schemes
        self.consumes = consumes
        self.produces = produces

        self.mm_qs_converter = (
            mm_query_string_converter_registry
            or query_string_converter_registry
        ).convert
        self.mm_rb_converter = (
            mm_request_body_converter_registry
            or request_body_converter_registry
        ).convert
        self.mm_hd_converter = (
            mm_headers_converter_registry
            or headers_converter_registry
        ).convert
        self.mm_rs_converter = (
            mm_response_converter_registry
            or response_converter_registry
        ).convert

        self.flask_converters_to_swagger_types = {
            'uuid': sw.string,
            'string': sw.string,
            'int': sw.integer,
            'float': sw.number
        }

        self.authenticator_converters = {
            HeaderApiKeyAuthenticator: _convert_header_api_key_authenticator
        }

        self.default_response_schema = default_response_schema

    def register_flask_converter_to_swagger_type(self, flask_converter, swagger_type):
        self.flask_converters_to_swagger_types[flask_converter] = swagger_type

    def register_authenticator_converter(self, authenticator_type, converter):
        self.authenticator_converters[authenticator_type] = converter

    def generate(self, framer):
        security_definitions = self._get_security_definitions(paths=framer.paths)
        definitions = self._get_definitions(paths=framer.paths)
        # parameters = self._get_common_parameters()

        paths = self._get_paths(
            paths=framer.paths,
            definitions=definitions,
            security_definitions={}
        )

        swagger = {
            sw.swagger: self._get_version(),
            sw.info: self._get_info(),
            sw.host: self._get_host(),
            sw.schemes: self._get_schemes(),
            sw.consumes: self._get_consumes(),
            sw.produces: self._get_produces(),
            sw.security_definitions: security_definitions,
            sw.paths: paths,
            sw.definitions: definitions
        }

        return swagger

    def _get_version(self):
        return '2.0'

    def _get_host(self):
        return self.host

    def _get_info(self):
        return {}

    def _get_schemes(self):
        return list(self.schemes)

    def _get_consumes(self):
        return list(self.consumes)

    def _get_produces(self):
        return list(self.produces)

    def _get_security_definitions(self, paths):
        security_definitions = {}

        authenticators = set(
            d.authenticate
            for d in self._iterate_path_definitions(paths=paths)
            if d.authenticate
        )

        # for d in self._iterate_path_definitions(paths=paths):
        #     if d.authenticate:
        #         authenticators.add(d.authenticate)

        for authenticator in authenticators:
            klass = authenticator.__class__
            converter = self.authenticator_converters[klass]
            key, definition = converter(authenticator=authenticator)
            security_definitions[key] = definition

        return security_definitions

    # def _get_common_parameters(self):
    #     pass

    def _get_paths(self, paths, definitions, security_definitions):
        path_definitions = {}

        for path, methods in paths.items():
            path_definition = {}

            swagger_path, path_args = _format_path_for_swagger(path)
            path_definitions[swagger_path] = path_definition

            if path_args:
                path_definition[sw.parameters] = [
                    {
                        sw.name: path_arg.name,
                        sw.required: True,
                        sw.in_: sw.path,
                        sw.type_: self.flask_converters_to_swagger_types[path_arg.type]

                    }
                    for path_arg in path_args
                ]

            for method, d in methods.items():
                responses_definition = {
                    sw.default: {
                        sw.schema: {
                            sw.ref: _get_ref(get_schema_title(self.default_response_schema))
                        }
                    }
                }

                if d.marshal:
                    for status_code, schema in d.marshal.items():
                        response_definition = {
                            sw.schema: {sw.ref: _get_ref(get_schema_title(schema))}
                        }

                        responses_definition[str(status_code)] = response_definition

                parameters_definition = []

                if d.query_string:
                    parameters_definition.extend(
                        convert_jsonschema_to_list_of_parameters(
                            self.mm_qs_converter(d.query_string),
                            in_=sw.query
                        )
                    )

                if d.request_body:
                    schema = d.request_body

                    parameters_definition.append({
                        sw.name: schema.__class__.__name__,
                        sw.in_: sw.body,
                        sw.required: True,
                        sw.schema: {sw.ref: _get_ref(get_schema_title(schema))}
                    })

                if d.headers:
                    parameters_definition.extend(
                        convert_jsonschema_to_list_of_parameters(
                            self.mm_hd_converter(d.headers),
                            in_=sw.header
                        )
                    )

                method_lower = method.lower()
                path_definition[method_lower] = {
                    sw.operation_id: d.func.__name__,
                    sw.responses: responses_definition
                }

                if d.func.__doc__:
                    path_definition[method_lower][sw.description] = d.func.__doc__

                if parameters_definition:
                    path_definition[method_lower][sw.parameters] = parameters_definition

                if d.authenticate:
                    name, _ = _convert_header_api_key_authenticator(d.authenticate)
                    path_definition[method_lower][sw.security] = {
                        name: []
                    }

        return path_definitions

    def _get_definitions(self, paths):
        all_schemas = set()

        converted = []

        all_schemas.add(self.default_response_schema)
        converted.append(self.mm_rs_converter(self.default_response_schema))

        for d in self._iterate_path_definitions(paths=paths):
            if d.marshal:
                for schema in d.marshal.values():
                    if schema not in all_schemas:
                        converted.append(self.mm_rs_converter(schema))
                    all_schemas.add(schema)

            if d.request_body:
                schema = d.request_body

                if schema not in all_schemas:
                    converted.append(self.mm_rb_converter(schema))

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
