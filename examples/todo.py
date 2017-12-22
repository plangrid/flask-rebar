from flask import Flask
from marshmallow import fields

from plangrid.flask_toolbox import Framer, bootstrap_app_with_framer, http_errors
from plangrid.flask_toolbox.validation import ListOf, RequestSchema, ResponseSchema


framer = Framer()

# Just a mock database, for demonstration purposes
todo_id_sequence = 0
todo_database = {}


# The framer relies heavily on Marshmallow.
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


@framer.handles(
    path='/todos',
    method='POST',
    request_body_schema=CreateTodoSchema(),

    # This dictionary tells framer which schema to use for which response code.
    # This is a little ugly, but tremendously helpful for generating swagger.
    marshal_schemas={
        201: TodoSchema()
    }
)
def create_todo():
    global todo_id_sequence, todo_database

    # The body is eagerly validated with the `request_body_schema` provided in
    # the decorator. The resulting parameters are now available here:
    todo = framer.validated_body

    todo_id_sequence += 1

    todo['id'] = todo_id_sequence
    todo_database[todo_id_sequence] = todo

    # The return value may be an object to encoded as JSON or a tuple where
    # the first item is the value to be encoded as JSON and the second is
    # the HTTP response code. In the case where no response code is included,
    # 200 is assumed.
    return todo, 201


@framer.handles(
    path='/todos',
    method='GET',
    query_string_schema=GetTodoListSchema(),

    # If the value for this is not a dictionary, the response code is assumed
    # to be 200
    marshal_schemas=ListOf(TodoSchema)()
)
def get_todos():
    global todo_database

    # Just like validated_body, query string parameters are eagerly validated
    # and made available here. Flask-toolbox does treats a request body and
    # query string parameters as two separate sources, and currently does not
    # implement any abstraction on top of them.
    args = framer.validated_args

    todos = todo_database.values()

    if 'complete' in args:
        todos = [t for t in todos if ['complete'] == args['complete']]

    # The `ListOf` helper above just nests the provided schema into "data"
    return {'data': todos}


@framer.handles(
    path='/todos/<int:todo_id>',
    method='PATCH',
    marshal_schemas=TodoSchema(),
    request_body_schema=UpdateTodoSchema()
)
def update_todo(todo_id):
    global todo_database

    if todo_id not in todo_database:
        raise http_errors.NotFound()

    params = framer.validated_body

    todo_database[todo_id].update(params)

    todo = todo_database[todo_id]

    return todo


def create_app(name):
    app = Flask(name)

    bootstrap_app_with_framer(app=app, framer=framer)

    # The ToolboxFramer includes a default authenticator, which does super
    # simple service-to-service authentication by looking for a shared secret
    # in the X-PG-Auth header. Here we define what that shared secret is.
    framer.default_authenticator.register_key(key='my-api-key')

    return app


if __name__ == '__main__':
    create_app(__name__).run()
