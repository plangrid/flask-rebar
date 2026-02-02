from typing import Any
from typing import Dict

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version  # type: ignore

import marshmallow
from marshmallow.fields import Field
from marshmallow.schema import Schema

from flask import current_app
from flask_rebar.validation import filter_dump_only, RequireOnDumpMixin


def set_data_key(field: Field, key: str) -> Field:
    field.data_key = key
    return field


def get_data_key(field: Field) -> str:
    if field.data_key:
        return field.data_key
    if field.name is None:
        raise ValueError("Field name cannot be None")
    return field.name


def load(schema: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    return schema.load(data)


def dump(schema: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Our wrapper for Schema.dump that includes optional validation.
    Note that as of Flask-Rebar 2.x (hence Marshmallow 3.x), Marshmallow's default behavior is to NOT validate on dump
    Accordingly, we are making validation "opt-in" here, which can be controlled at schema level with
    RequireOnDumpMixin or globally via validate_on_dump attribute of Rebar instance
    """
    try:
        force_validation = current_app.extensions["rebar"]["instance"].validate_on_dump
    except (
        RuntimeError
    ):  # running outside app context (some unit test cases, potentially ad hoc scripts)
        force_validation = False

    if isinstance(schema, RequireOnDumpMixin) or force_validation:
        try:
            # We do an initial schema.dump here in order to support arbitrary data objects (e.g., ORM objects, etc.)
            # and give us something we can pass to .load below
            # Since marshmallow 3 doesn't validate on dump, this has the effect of stripping unknown fields.
            result = schema.dump(data)
        except marshmallow.ValidationError:
            raise
        except Exception as e:
            raise marshmallow.ValidationError(str(e))

        # filter out "dump_only" fields before we call load - we are only calling load to validate data we are dumping
        # (We use load because that's how Marshmallow docs recommend doing this sort of validation, presumably because
        # @pre_load massaging of data could make otherwise invalid data valid.
        filtered = filter_dump_only(schema, result)
        schema.load(filtered.loadable)  # trigger validation
    else:
        result = schema.dump(data)
    return result


def exclude_unknown_fields(schema: Schema) -> Schema:
    schema.unknown = marshmallow.EXCLUDE
    return schema


# Marshmallow version detection for backward compatibility
MARSHMALLOW_VERSION_MAJOR = int(version("marshmallow").split(".")[0])


def is_schema_ordered(schema: Schema) -> bool:
    """
    Check if a schema should maintain field order.

    In Marshmallow 3.x, this is controlled by the 'ordered' attribute.
    In Marshmallow 4.x+, field order is always preserved (insertion order from dict).

    :param Schema schema: The schema to check
    :return: True if fields should maintain their order, False if they should be sorted
    :rtype: bool
    """
    if MARSHMALLOW_VERSION_MAJOR >= 4:
        # In Marshmallow 4+, fields are always ordered (insertion order)
        return True

    # In Marshmallow 3, check the 'ordered' attribute
    return getattr(schema, "ordered", False)
