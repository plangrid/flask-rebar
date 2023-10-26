from enum import Enum

from todo.database import todo_id_sequence, todo_database
from todo.app import rebar
from todo.app import registry
from todo.schemas import (
    CreateTodoSchema,
    GetTodoListSchema,
    TodoResourceSchema,
    TodoListSchema,
    UpdateTodoSchema,
)


@registry.handles(
    rule="/todos",
    method="POST",
    request_body_schema=CreateTodoSchema(),
    tags=["todo"],
    # This dictionary tells framer which schema to use for which response code.
    # This is a little ugly, but tremendously helpful for generating swagger.
    response_body_schema={
        201: TodoResourceSchema()
    },  # for versions <= 1.7.0, use marshal_schema
)
def create_todo():
    global todo_id_sequence, todo_database

    # The body is eagerly validated with the `request_body_schema` provided in
    # the decorator. The resulting parameters are now available here:
    todo = rebar.validated_body

    todo_id_sequence += 1

    todo["id"] = todo_id_sequence
    todo_database[todo_id_sequence] = todo

    # The return value may be an object to encoded as JSON or a tuple where
    # the first item is the value to be encoded as JSON and the second is
    # the HTTP response code. In the case where no response code is included,
    # 200 is assumed.
    return todo, 201


@registry.handles(
    rule="/todos",
    method="GET",
    query_string_schema=GetTodoListSchema(),
    tags=["todo"],
    # If the value for this is not a dictionary, the response code is assumed
    # to be 200
    response_body_schema=TodoListSchema(),  # for versions <= 1.7.0, use marshal_schema
)
def get_todos():
    global todo_database

    # Just like validated_body, query string parameters are eagerly validated
    # and made available here. Flask-toolbox does treats a request body and
    # query string parameters as two separate sources, and currently does not
    # implement any abstraction on top of them.
    args = rebar.validated_args

    todos = todo_database.values()

    if "complete" in args:
        todos = [t for t in todos if t["complete"] == args["complete"]]

    return todos


@registry.handles(
    rule="/todos/<todo_types:todo_type>",
    method="GET",
    query_string_schema=GetTodoListSchema(),
    tags=["todo"],
    # If the value for this is not a dictionary, the response code is assumed
    # to be 200
    response_body_schema=TodoListSchema(),  # for versions <= 1.7.0, use marshal_schema
)
def get_todos_by_type(todo_type):
    global todo_database

    # Just like validated_body, query string parameters are eagerly validated
    # and made available here. Flask-toolbox does treats a request body and
    # query string parameters as two separate sources, and currently does not
    # implement any abstraction on top of them.
    args = rebar.validated_args

    todos = todo_database.values()

    if "complete" in args:
        todos = [t for t in todos if t["complete"] == args["complete"]]
    todos = [t for t in todos if t["type"] == todo_type.name]

    return todos


@registry.handles(
    rule="/todos/<int:todo_id>",
    method="PATCH",
    response_body_schema=TodoResourceSchema(),  # for versions <= 1.7.0, use marshal_schema
    request_body_schema=UpdateTodoSchema(),
    tags=["todo"],
)
def update_todo(todo_id):
    global todo_database

    if todo_id not in todo_database:
        raise errors.NotFound()

    params = rebar.validated_body
    todo_database[todo_id].update(params)
    todo = todo_database[todo_id]

    return todo
