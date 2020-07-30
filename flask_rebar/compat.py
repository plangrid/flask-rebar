import abc
import collections
import sys
import pkg_resources

import marshmallow
from marshmallow import ValidationError

if int(sys.version_info[0]) == 2:
    Mapping = collections.Mapping
else:
    Mapping = collections.abc.Mapping

if sys.version_info >= (3, 4):
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta("ABC", (), {})

MARSHMALLOW_DISTRIBUTION = pkg_resources.get_distribution("marshmallow")
MARSHMALLOW_MAJOR_VERSION = int(MARSHMALLOW_DISTRIBUTION.version.split(".")[0])
MARSHMALLOW_V3 = MARSHMALLOW_MAJOR_VERSION == 3


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
    obj = schema.load(data)  # Deserialize to trigger validation
    return schema.dump(obj)


def exclude_unknown_fields(schema):
    schema.unknown = marshmallow.EXCLUDE
    return schema
