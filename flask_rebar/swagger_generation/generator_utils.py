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
from typing import (
    overload,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Set,
    Union,
    TYPE_CHECKING,
)

from flask_rebar.authenticators import Authenticator
from flask_rebar.utils.defaults import USE_DEFAULT
from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.swagger_generation.marshmallow_to_swagger import get_swagger_title
from marshmallow import Schema

if TYPE_CHECKING:
    from flask_rebar.rebar import HandlerRegistry
    from flask_rebar.rebar import PathDefinition


def get_key(obj: Dict[str, Any]) -> str:
    """
    Returns the key for a JSONSchema object that we can use to make a $ref.

    We're just enforcing that objects all have a title for now.

    :param dict obj:
    :rtype: str
    """
    return obj[sw.title]


def create_ref(*parts: str) -> str:
    """Create a reference from `parts`

    For example:

        assert create_ref("#", "definitions", "foo") == "#/definitions/foo"

    :param Tuple[str] parts:
    :rtype: str
    """
    return "/".join(parts)


def get_ref_schema(base: str, schema: Schema) -> Dict[str, Any]:
    """Create a JSONSchema object that is a reference to `schema`

    :param base: base string for references, e.g. "#/definitions"
    :param schema:
    :return:
    """
    ref: Dict[str, Any] = {sw.ref: create_ref(base, get_swagger_title(schema))}
    return ref if not schema.many else {sw.type_: sw.array, sw.items: ref}


def get_response_description(schema: Schema) -> str:
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


def flatten(schema: Dict[str, Any], base: str) -> Tuple[Dict[str, str], Dict[str, Any]]:
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
    definitions: Dict[str, Any] = {}
    schema = _flatten(schema=schema, definitions=definitions, base=base)
    return schema, definitions


def _flatten(
    schema: Dict[str, Any], definitions: Dict[str, Any], base: str
) -> Dict[str, str]:
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


def _get_subschema_keyword(schema: Dict[str, Any]) -> Optional[str]:
    for keyword in (sw.any_of, sw.one_of, sw.all_of):
        if keyword in schema:
            return keyword
    return None


_PATH_REGEX = re.compile("<((?P<type>.+?):)?(?P<name>.+?)>")
PathArgument = namedtuple("PathArgument", ["name", "type"])


def format_path_for_swagger(path: str) -> Tuple[str, Tuple[PathArgument, ...]]:
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


def verify_parameters_are_the_same(
    a: List[Dict[str, Any]], b: List[Dict[str, Any]]
) -> None:
    def get_sort_key(parameter: Dict[str, Any]) -> str:
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
    registry: "HandlerRegistry",
    base: str,
    default_response_schema: Schema,
    response_converter: Callable[[Schema], Dict[str, Any]],
    request_body_converter: Callable[[Schema], Dict[str, Any]],
) -> Dict[str, Any]:
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


def get_unique_authenticators(registry: "HandlerRegistry") -> Set[Authenticator]:
    authenticators = {
        authenticator
        for d in iterate_path_definitions(paths=registry.paths)
        for authenticator in d.authenticators
        if authenticator is not None and authenticator is not USE_DEFAULT
    }

    for authenticator in registry.default_authenticators:
        if authenticator is not None:
            authenticators.add(authenticator)

    return authenticators


def iterate_path_definitions(
    paths: Dict[str, Dict[str, "PathDefinition"]]
) -> Iterator["PathDefinition"]:
    """Iterate over all `PathDefinition` instances in `paths`

    :param dict[str, dict[str, flask_rebar.rebar.PathDefinition]] paths:
    :return Iterator[PathDefinition]
    """
    for methods in paths.values():
        yield from methods.values()


@overload
def recursively_convert_dict_to_ordered_dict(obj: Dict) -> OrderedDict:
    ...


@overload
def recursively_convert_dict_to_ordered_dict(obj: List[Dict]) -> List[OrderedDict]:
    ...


@overload
def recursively_convert_dict_to_ordered_dict(
    obj: List[OrderedDict],
) -> List[OrderedDict]:
    ...


def recursively_convert_dict_to_ordered_dict(
    obj: Union[Dict, List[Dict], List[OrderedDict]]
) -> Union[OrderedDict, List[OrderedDict]]:
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
