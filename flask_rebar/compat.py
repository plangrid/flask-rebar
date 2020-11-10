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
    try:
        result = schema.dump(data)
    except Exception as e:
        if isinstance(e, marshmallow.ValidationError):
            raise
        raise marshmallow.ValidationError(str(e))
    schema.load(result)
    return result


def exclude_unknown_fields(schema):
    schema.unknown = marshmallow.EXCLUDE
    return schema
