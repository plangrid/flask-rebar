# Rebar relies heavily on Marshmallow.
# These schemas will be used to validate incoming data, marshal outgoing
# data, and to automatically generate a Swagger specification.

from flask_rebar.validation import RequestSchema, ResponseSchema
from flask_rebar.swagger_generation.marshmallow_to_swagger import EnumField
from marshmallow import fields, pre_dump, pre_load

from .converters import TodoType


class CreateTodoSchema(RequestSchema):
    complete = fields.Boolean(required=True)
    description = fields.String(required=True)
    type = EnumField(TodoType, load_default=TodoType.user)


class UpdateTodoSchema(CreateTodoSchema):
    # This schema provides an example of one way to re-use another schema while making some fields optional
    # a "partial" schema in Marshmallow parlance:
    def __init__(self, **kwargs):
        super_kwargs = dict(kwargs)
        partial_arg = super_kwargs.pop("partial", True)
        # Note: if you only want to mark some fields as partial, pass partial= a collection of field names, e.g.,:
        # partial_arg = super_kwargs.pop('partial', ('description', ))
        super().__init__(partial=partial_arg, **super_kwargs)


class GetTodoListSchema(RequestSchema):
    complete = fields.Boolean()


class TodoSchema(ResponseSchema):
    id = fields.Integer(required=True)
    complete = fields.Boolean(required=True)
    description = fields.String(required=True)
    type = EnumField(TodoType, required=True)


class TodoResourceSchema(ResponseSchema):
    data = fields.Nested(TodoSchema)

    @pre_dump
    @pre_load
    def envelope_in_data(self, data, **kwargs):
        if type(data) is not dict or "data" not in data.keys():
            return {"data": data}
        else:
            return data


class TodoListSchema(ResponseSchema):
    data = fields.Nested(TodoSchema, many=True)

    @pre_dump
    @pre_load
    def envelope_in_data(self, data, **kwargs):
        if type(data) is not dict or "data" not in data.keys():
            return {"data": data}
        else:
            return data
