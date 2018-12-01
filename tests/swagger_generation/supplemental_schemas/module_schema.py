import marshmallow as m


class ModuleSchema(m.Schema):
    name = m.fields.String()
