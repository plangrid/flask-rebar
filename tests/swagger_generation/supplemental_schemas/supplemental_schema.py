import marshmallow as m


class SupplementalSchema(m.Schema):
    name = m.fields.String()
