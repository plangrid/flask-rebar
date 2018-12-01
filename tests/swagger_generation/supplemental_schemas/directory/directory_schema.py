import marshmallow as m


class DirectorySchema(m.Schema):
    name = m.fields.String()
