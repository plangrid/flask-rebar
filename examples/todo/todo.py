from flask import Flask
from marshmallow import fields, pre_dump, Schema

from flask_rebar import Rebar, errors, HeaderApiKeyAuthenticator
from flask_rebar.validation import RequestSchema, ResponseSchema


rebar = Rebar()
registry = rebar.create_handler_registry()

# Just a mock database, for demonstration purposes
todo_id_sequence = 0
todo_database = {}


# Rebar relies heavily on Marshmallow.
# These schemas will be used to validate incoming data, marshal outgoing
# data, and to automatically generate a Swagger specification.

class CreateTodoSchema(RequestSchema):
    complete = fields.Boolean(required=True)
    description = fields.String(required=True)


class UpdateTodoSchema(RequestSchema):
    complete = fields.Boolean()
    description = fields.String()


class GetTodoListSchema(RequestSchema):
    complete = fields.Boolean()


class TodoSchema(ResponseSchema):
    id = fields.Integer(required=True)
    complete = fields.Boolean(required=True)
    description = fields.String(required=True)


class TodoResourceSchema(ResponseSchema):
    data = fields.Nested(TodoSchema)

    @pre_dump
    def envelope_in_data(self, data):
        return {'data': data}


class TodoListSchema(ResponseSchema):
    data = fields.Nested(TodoSchema, many=True)

    @pre_dump
    def envelope_in_data(self, data):
        return {'data': data}


@registry.handles(
    rule='/todos',
    method='POST',
    request_body_schema=CreateTodoSchema(),

    # This dictionary tells framer which schema to use for which response code.
    # This is a little ugly, but tremendously helpful for generating swagger.
    marshal_schema={
        201: TodoResourceSchema()
    }
)
def create_todo():
    global todo_id_sequence, todo_database

    # The body is eagerly validated with the `request_body_schema` provided in
    # the decorator. The resulting parameters are now available here:
    todo = rebar.validated_body

    todo_id_sequence += 1

    todo['id'] = todo_id_sequence
    todo_database[todo_id_sequence] = todo

    # The return value may be an object to encoded as JSON or a tuple where
    # the first item is the value to be encoded as JSON and the second is
    # the HTTP response code. In the case where no response code is included,
    # 200 is assumed.
    return todo, 201


@registry.handles(
    rule='/todos',
    method='GET',
    query_string_schema=GetTodoListSchema(),

    # If the value for this is not a dictionary, the response code is assumed
    # to be 200
    marshal_schema=TodoListSchema()
)
def get_todos():
    global todo_database

    # Just like validated_body, query string parameters are eagerly validated
    # and made available here. Flask-toolbox does treats a request body and
    # query string parameters as two separate sources, and currently does not
    # implement any abstraction on top of them.
    args = rebar.validated_args

    todos = todo_database.values()

    if 'complete' in args:
        todos = [t for t in todos if ['complete'] == args['complete']]

    return todos


@registry.handles(
    rule='/todos/<int:todo_id>',
    method='PATCH',
    marshal_schema=TodoResourceSchema(),
    request_body_schema=UpdateTodoSchema()
)
def update_todo(todo_id):
    global todo_database

    if todo_id not in todo_database:
        raise errors.NotFound()

    params = rebar.validated_body

    todo_database[todo_id].update(params)

    todo = todo_database[todo_id]

    return todo


def create_app(name):
    app = Flask(name)

    authenticator = HeaderApiKeyAuthenticator(header='X-MyApp-Key')
    # The HeaderApiKeyAuthenticator does super simple authentication, designed for
    # service-to-service authentication inside of a protected network, by looking for a
    # shared secret in the specified header. Here we define what that shared secret is.
    authenticator.register_key(key='my-api-key')
    registry.set_default_authenticator(authenticator=authenticator)

    rebar.init_app(app=app)

    return app


if __name__ == '__main__':
    create_app(__name__).run()
