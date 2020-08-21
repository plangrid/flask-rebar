import marshmallow


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
