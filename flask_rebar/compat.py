from collections import Mapping

import marshmallow

from flask import g
from flask_rebar.validation import filter_dump_only, RequireOnDumpMixin


def set_data_key(field, key):
    field.data_key = key
    return field


def get_data_key(field):
    if field.data_key:
        return field.data_key
    return field.name


def load(schema, data):
    return schema.load(data)


def dump(schema, data):
    """
    Our wrapper for Schema.dump that includes optional validation.
    Note that as of Flask-Rebar 2.x (hence Marshmallow 3.x), Marshmallow's default behavior is to NOT validate on dump
    Accordingly, we are making validation "opt-in" here, which can be controlled at schema level with
    RequireOnDumpMixin or globally via rebar.set_validate_on_dump(True)
    CAVEAT: Regardless of the Schema's "unknown" field setting, unknown fields will behave like EXCLUDE (ignored) here.
    """
    try:
        force_validation = getattr(g, "validate_on_dump", False)
    except RuntimeError:  # running outside app context (some unit test cases, potentially ad hoc scripts)
        force_validation = False

    if isinstance(schema, RequireOnDumpMixin) or force_validation:
        try:
            # We do an initial schema.dump here in order to support arbitrary data objects (e.g., ORM objects, etc.)
            # and give us something we can pass to .load below
            # Since marshmallow 3 doesn't validate on dump, this has the effect of stripping unknown fields.
            result = schema.dump(data)
        except Exception as e:
            if isinstance(e, marshmallow.ValidationError):
                raise
            raise marshmallow.ValidationError(str(e))

        # filter out "dump_only" fields before we call load - we are only calling load to validate data we are dumping
        # (We use load because that's how Marshmallow docs recommend doing this sort of validation, presumably because
        # @pre_load massaging of data could make otherwise invalid data valid.
        filtered = filter_dump_only(schema, result)
        validated = schema.dump(
            schema.load(filtered.loadable)
        )  # validation (and supply things like missing defaults)

        # and finally add back the dump_only data we had to filter out during validation.
        _recombine_filtered_dicts(validated, filtered.dump_only)
        return validated
    else:
        result = schema.dump(data)
    return result


def exclude_unknown_fields(schema):
    schema.unknown = marshmallow.EXCLUDE
    return schema


def _recombine_filtered_dicts(result, filter_results):
    """
    For use in our "validated dump" case
    Fold anything that was "dump_only" (passed as "filter_results") back into result dict (or list of dicts).
    WILL MODIFY result IN PLACE!
    """
    if isinstance(filter_results, list):
        for i, filtered_val in enumerate(filter_results):
            _recombine_filtered_dicts(result[i], filter_results[i])
    else:
        for k, v in filter_results.items():
            if isinstance(v, Mapping) or isinstance(v, list):
                _recombine_filtered_dicts(result[k], v)
            else:
                result[k] = filter_results[k]
    return result
