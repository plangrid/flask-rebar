"""
    Generator Utilities
    ~~~~~~~~~~~~~~~~~~~

    Helper functions shared by multiple Swagger Generators.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import copy
import re
from collections import namedtuple, OrderedDict

from flask_rebar.utils.deprecation import deprecated
from flask_rebar.utils.defaults import USE_DEFAULT
from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.swagger_generation.marshmallow_to_swagger import get_swagger_title
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    AuthenticatorConverterRegistry,
)


def get_key(obj):
    """
    Returns the key for a JSONSchema object that we can use to make a $ref.

    We're just enforcing that objects all have a title for now.

    :param dict obj:
    :rtype: str
    """
    return obj[sw.title]


def create_ref(*parts):
    """Create a reference from `parts`

    For example:

        assert create_ref("#", "definitions", "foo") == "#/definitions/foo"

    :param Tuple[str] parts:
    :rtype: str
    """
    return "/".join(parts)


def get_ref_schema(base, schema):
    """Create a JSONSchema object that is a reference to `schema`

    :param schema:
    :param base: base string for references, e.g. "#/definitions"
    :return:
    """
    ref = {sw.ref: create_ref(base, get_swagger_title(schema))}
    return ref if not schema.many else {sw.type_: sw.array, sw.items: ref}


def get_response_description(schema):
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


def flatten(schema, base):
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
    :param str base: Base string for references, e.g. "#/definitions"
    :rtype: tuple(dict, dict)
    :returns: A tuple where the first item is the input object with any nested
    objects replaces with references, and the second item is the flattened
    definitions dictionary.
    """
    schema = copy.deepcopy(schema)
    definitions = {}
    schema = _flatten(schema=schema, definitions=definitions, base=base)
    return schema, definitions


def _flatten(schema, definitions, base):
    schema_type = schema.get(sw.type_)
    subschema_keyword = _get_subschema_keyword(schema)

    if schema_type == sw.object_:
        properties = schema.get(sw.properties, {})
        for key, prop in properties.items():
            properties[key] = _flatten(schema=prop, definitions=definitions, base=base)

    elif schema_type == sw.array:
        schema[sw.items] = _flatten(
            schema=schema[sw.items], definitions=definitions, base=base
        )

    elif subschema_keyword:
        subschemas = schema[subschema_keyword]
        for i, subschema in enumerate(subschemas):
            subschemas[i] = _flatten(
                schema=subschema, definitions=definitions, base=base
            )

    if sw.title in schema:
        definitions_key = get_key(schema)
        definitions[definitions_key] = schema
        schema = {sw.ref: create_ref(base, definitions_key)}

    return schema


def _get_subschema_keyword(schema):
    for keyword in (sw.any_of, sw.one_of, sw.all_of):
        if keyword in schema:
            return keyword


_PATH_REGEX = re.compile("<((?P<type>.+?):)?(?P<name>.+?)>")
PathArgument = namedtuple("PathArgument", ["name", "type"])


def format_path_for_swagger(path):
    """
    Flask and Swagger represent paths differently - this parses a Flask path
    to its Swagger form. This also extracts what the arguments in the flask
    path are, so we can represent them as parameters in Swagger.

    :param str path:
    :rtype: tuple(str, tuple(_PathArgument))
    """
    matches = list(_PATH_REGEX.finditer(path))

    args = tuple(
        PathArgument(name=match.group("name"), type=match.group("type") or "string")
        for match in matches
    )

    subbed_path = _PATH_REGEX.sub(
        repl=lambda match: "{{{}}}".format(match.group("name")), string=path
    )
    return subbed_path, args


@deprecated(eol_version="2.0")
def convert_header_api_key_authenticator(authenticator):
    """
    Converts a HeaderApiKeyAuthenticator object to a Swagger definition.

    :param flask_rebar.authenticators.HeaderApiKeyAuthenticator authenticator:
    :rtype: tuple(str, dict)
    :returns: Tuple where the first item is a name for the authenticator, and
    the second item is a Swagger definition for it.
    """
    key = authenticator.name
    definition = {
        sw.name: authenticator.header,
        sw.in_: sw.header,
        sw.type_: sw.api_key,
    }
    return key, definition


def verify_parameters_are_the_same(a, b):
    def get_sort_key(parameter):
        return parameter[sw.name]

    sorted_a = sorted(a, key=get_sort_key)
    sorted_b = sorted(b, key=get_sort_key)

    if sorted_a != sorted_b:
        msg = (
            "Swagger generation does not support Flask url "
            "converters that map to different Swagger types!"
        )
        raise ValueError(msg)


def get_unique_schema_definitions(
    registry, base, default_response_schema, response_converter, request_body_converter
):
    """Extract a map of unique schema definitions for all marshal schemas and responses schemas in `registry`

    :param flask_rebar.rebar.HandlerRegistry registry:
    :param str base: Base string for references, e.g. "#/definitions"
    :param marshmallow.Schema default_response_schema:
    :param typing.Callable[[marshmallow.Schema], dict] response_converter:
    :param typing.Callable[[marshmallow.Schema], dict] request_body_converter:
    :rtype: dict
    """
    all_schemas = set()

    converted = []

    all_schemas.add(default_response_schema)
    converted.append(response_converter(default_response_schema))

    for d in iterate_path_definitions(paths=registry.paths):
        if d.response_body_schema:
            for schema in d.response_body_schema.values():
                if schema is None:
                    # Responses that don't have a response body have None
                    # for a schema
                    continue

                if schema not in all_schemas:
                    converted.append(response_converter(schema))
                all_schemas.add(schema)

        if d.request_body_schema:
            schema = d.request_body_schema

            if schema not in all_schemas:
                converted.append(request_body_converter(schema))

            all_schemas.add(schema)

    flattened = {}

    for obj in converted:
        _, flattened_definitions = flatten(obj, base)
        flattened.update(flattened_definitions)

    return flattened


def get_unique_authenticators(registry):
    authenticators = set(
        authenticator
        for d in iterate_path_definitions(paths=registry.paths)
        for authenticator in d.authenticators
        if authenticator is not None and authenticator is not USE_DEFAULT
    )

    for authenticator in registry.default_authenticators:
        if authenticator is not None:
            authenticators.add(authenticator)

    return authenticators


def iterate_path_definitions(paths):
    """Iterate over all `PathDefinition` instances in `paths`

    :param dict[str, dict[str, flask_rebar.rebar.PathDefinition]] paths:
    :return Iterator[PathDefinition]
    """
    for methods in paths.values():
        for definition in methods.values():
            yield definition


def recursively_convert_dict_to_ordered_dict(obj):
    """Recursively converts a dictionary into and OrderedDict"""
    if isinstance(obj, dict):
        sorted_dict = OrderedDict(sorted(obj.items(), key=lambda i: i[0]))
        for key, val in obj.items():
            sorted_dict[key] = recursively_convert_dict_to_ordered_dict(val)
        return sorted_dict
    elif isinstance(obj, list):
        return [recursively_convert_dict_to_ordered_dict(item) for item in obj]
    else:
        return obj


AuthenticatorConverter = AuthenticatorConverterRegistry  # deprecated alias
