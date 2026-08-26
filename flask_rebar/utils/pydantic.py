"""Pydantic models for Flask-Rebar request validation and response marshaling.

Install this module's optional dependency with ``flask-rebar[pydantic]``.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from functools import cached_property
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

if sys.version_info >= (3, 10):
    from types import UnionType
else:  # pragma: no cover - Python < 3.10
    UnionType = None

import marshmallow
from flask_rebar.rebar import get_validated_args, get_validated_body, get_validated_headers
from flask_rebar.swagger_generation import swagger_words as sw
from flask_rebar.swagger_generation.marshmallow_to_swagger import (
    MarshmallowConverter,
    headers_converter_registry,
    query_string_converter_registry,
    request_body_converter_registry,
    response_converter_registry,
)
from werkzeug.datastructures import MultiDict

try:
    from pydantic import (
        BaseModel,
        ConfigDict,
        PlainSerializer,
        SerializationInfo,
        WithJsonSchema,
        model_serializer,
    )
    from pydantic import ValidationError as PydanticValidationError
    from pydantic.alias_generators import to_camel
except ModuleNotFoundError as error:
    if error.name == "pydantic":
        raise ImportError(
            "Pydantic support requires the optional dependency. "
            "Install flask-rebar[pydantic]."
        ) from error
    raise


ModelType = TypeVar("ModelType", bound=BaseModel)


class ApiModel(BaseModel):
    """Base API model with strict, unknown-rejecting request fields."""

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class CamelCaseApiModel(ApiModel):
    """:class:`ApiModel` that also aliases fields to camelCase."""

    model_config = ConfigDict(alias_generator=to_camel)


DateTime = Annotated[
    datetime,
    PlainSerializer(lambda value: value.isoformat(), return_type=str, when_used="json"),
    WithJsonSchema({"type": "string", "format": "date-time"}, mode="serialization"),
]
"""A datetime annotation that preserves offsets in serialized API responses."""


class OmitNone(BaseModel):
    """Mixin that omits ``None`` values when Flask-Rebar serializes a response."""

    @model_serializer(mode="wrap")
    # No return annotation: Pydantic uses it to build the *serialization* JSON Schema, 
    # and an explicit type here (even `Any`) breaks introspection for wrap-mode-serializers.
    def _omit_none(self, handler: Any, info: SerializationInfo):  # type: ignore[no-untyped-def]
        data = handler(self)
        if not _omit_none_active(info):
            return data
        return {key: value for key, value in data.items() if value is not None}


_OMIT_NONE = "flask_rebar_omit_none"


def _omit_none_active(info: SerializationInfo) -> bool:
    return bool((info.context or {}).get(_OMIT_NONE))


class PydanticSchema(marshmallow.Schema):
    """A Marshmallow-shaped adapter around a Pydantic model."""

    model: ClassVar[type[BaseModel]]

    # skip validate_on_dump in compat.dump
    dump_validates: ClassVar[bool] = True

    @cached_property
    def _known_keys(self) -> frozenset[str]:
        """Every field name and alias the model accepts."""
        fields = self.model.model_fields
        return frozenset(fields) | {
            field.alias for field in fields.values() if field.alias
        }

    @cached_property
    def _sequence_keys(self) -> frozenset[str]:
        """The subset of :attr:`_known_keys` whose fields accept a sequence."""
        return frozenset(
            key
            for name, field in self.model.model_fields.items()
            for key in (name, field.alias)
            if key and _accepts_sequence(field.annotation)
        )

    def load(
        self,
        data: Any,
        *,
        many: bool | None = None,
        partial: Any = None,
        unknown: str | None = None,
    ) -> BaseModel:
        """Validate data with Pydantic and return its model instance."""
        del many, partial
        if isinstance(data, MultiDict):
            data = self._flatten_multidict(data)
        if (unknown or self.unknown) == marshmallow.EXCLUDE and isinstance(
            data, Mapping
        ):
            known = self._known_keys
            data = {key: value for key, value in data.items() if key in known}
        try:
            return self.model.model_validate(data)
        except PydanticValidationError as error:
            raise marshmallow.ValidationError(_marshmallow_errors(error)) from error

    def _flatten_multidict(self, data: MultiDict) -> dict[str, Any]:
        sequence_keys = self._sequence_keys
        return {
            key: (values if key in sequence_keys else values[0])
            for key, values in data.lists()
        }

    def dump(self, obj: Any, *, many: bool | None = None) -> Any:
        """Serialize a model, mapping, or attribute-bearing object with Pydantic."""
        if many:
            return [self.dump(item) for item in obj]
        if isinstance(obj, self.model):
            model = obj
        else:
            if isinstance(obj, Mapping):
                known = self._known_keys
                obj = {key: value for key, value in obj.items() if key in known}
            model = self.model.model_validate(obj)
        return model.model_dump(mode="json", by_alias=True, context={_OMIT_NONE: True})


def schema_for(model: type[ModelType]) -> PydanticSchema:
    """Return the cached Flask-Rebar schema adapter for a Pydantic model."""
    schema = _SCHEMA_CACHE.get(model)
    if schema is None:
        schema_class = type(component_name(model), (PydanticSchema,), {"model": model})
        schema = schema_class()
        json_schema = _openapi_schema(model)
        required = set(json_schema.get(sw.required, ()))
        schema.fields = schema.declared_fields = {
            name: _JsonSchemaField(
                property_schema, data_key=name, required=name in required
            )
            for name, property_schema in json_schema.get(sw.properties, {}).items()
        }
        _SCHEMA_CACHE[model] = schema
    return schema


def validated_body(model: type[ModelType]) -> ModelType:
    """Return Flask-Rebar's validated request body with its Pydantic type."""
    del model
    return cast(ModelType, get_validated_body())


def validated_args(model: type[ModelType]) -> ModelType:
    """Return Flask-Rebar's validated query arguments with their Pydantic type."""
    del model
    return cast(ModelType, get_validated_args())


def validated_headers(model: type[ModelType]) -> ModelType:
    """Return Flask-Rebar's validated request headers with their Pydantic type."""
    del model
    return cast(ModelType, get_validated_headers())


def openapi_schema(
    model: type[BaseModel], mode: Literal["validation", "serialization"] = "validation"
) -> dict[str, Any]:
    """Build a Pydantic JSON Schema suitable for Flask-Rebar's Swagger converter."""
    return deepcopy(_openapi_schema(model, mode))


def _openapi_schema(
    model: type[BaseModel], mode: Literal["validation", "serialization"] = "validation"
) -> dict[str, Any]:
    """Return the shared, cached JSON Schema. Callers must not mutate it."""
    key = (model, mode)
    cached = _OPENAPI_SCHEMA_CACHE.get(key)
    if cached is not None:
        return cached
    raw_schema = model.model_json_schema(mode=mode, ref_template="{model}")
    definitions = raw_schema.pop("$defs", {})
    schema: dict[str, Any] = _inline_refs(raw_schema, definitions, ())
    _OPENAPI_SCHEMA_CACHE[key] = schema
    return schema


def component_name(model: type[BaseModel]) -> str:
    """Return an OpenAPI-safe component name for a Pydantic model."""
    return _INVALID_NAME_CHARS.sub("", model.__name__)


def _accepts_sequence(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin in (list, set, tuple, frozenset):
        return True
    if origin is UnionType or origin is Union:
        return any(_accepts_sequence(argument) for argument in get_args(annotation))
    return False


def _marshmallow_errors(error: PydanticValidationError) -> dict[Any, Any]:
    errors: dict[Any, Any] = {}
    for item in error.errors():
        location = item["loc"] or ("_schema",)
        target = errors
        for part in location[:-1]:
            target = target.setdefault(part, {})
        target.setdefault(location[-1], []).append(item["msg"])
    return errors


_SCHEMA_CACHE: dict[type[BaseModel], PydanticSchema] = {}
_OPENAPI_SCHEMA_CACHE: dict[tuple[type[BaseModel], str], dict[str, Any]] = {}
_INVALID_NAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")
_PROPERTY_MAP_KEYS = ("properties", "patternProperties", "$defs")


class _JsonSchemaField(marshmallow.fields.Field):
    """A placeholder Marshmallow field carrying a Pydantic JSON Schema property."""

    def __init__(self, json_schema: dict[str, Any], **kwargs: Any) -> None:
        self.json_schema = json_schema
        super().__init__(**kwargs)


def _inline_refs(node: Any, definitions: dict[str, Any], stack: tuple[str, ...]) -> Any:
    if isinstance(node, list):
        return [_inline_refs(item, definitions, stack) for item in node]
    if not isinstance(node, dict):
        return node

    reference = node.get("$ref")
    if reference is not None:
        if reference in stack:
            return {sw.type_: sw.object_}
        merged = {
            **definitions.get(reference, {}),
            **{key: value for key, value in node.items() if key != "$ref"},
        }
        return _inline_refs(merged, definitions, (*stack, reference))

    node = {
        key: (
            {
                name: _inline_refs(schema, definitions, stack)
                for name, schema in value.items()
            }
            if key in _PROPERTY_MAP_KEYS and isinstance(value, dict)
            else _inline_refs(value, definitions, stack)
        )
        for key, value in node.items()
    }

    if sw.title in node:
        if node.get(sw.type_) != sw.object_:
            del node[sw.title]
        else:
            node[sw.title] = _INVALID_NAME_CHARS.sub("", str(node[sw.title]))
    return node


class _PydanticSchemaConverter(MarshmallowConverter):
    MARSHMALLOW_TYPE = PydanticSchema

    def __init__(self, mode: Literal["validation", "serialization"]) -> None:
        self.mode = mode

    def convert(self, obj: PydanticSchema, context: Any) -> dict[str, Any]:
        del context
        return openapi_schema(obj.model, mode=self.mode)


class _JsonSchemaFieldConverter(MarshmallowConverter):
    MARSHMALLOW_TYPE = _JsonSchemaField

    def convert(self, obj: _JsonSchemaField, context: Any) -> dict[str, Any]:
        del context
        return dict(obj.json_schema)


request_body_converter_registry.register_type(_PydanticSchemaConverter("validation"))
response_converter_registry.register_type(_PydanticSchemaConverter("serialization"))
query_string_converter_registry.register_type(_JsonSchemaFieldConverter())
headers_converter_registry.register_type(_JsonSchemaFieldConverter())
