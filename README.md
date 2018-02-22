Flask-Rebar
===========

Flask-Rebar combines flask, marshmallow, and swagger for robust REST services.


Features
--------

- **Request and Response Validation** - Flask-Rebar relies on schemas from the popular [marshmallow](https://marshmallow.readthedocs.io/en/latest/) to validate incoming requests and marshal outgoing responses.
- **Automatic Swagger Generation** - The same schemas used for validation and marshaling are used to automatically generate OpenAPI specifications (a.k.a. Swagger). This also means automatic documentation via [Swagger UI](https://swagger.io/swagger-ui/).
- **Error Handling** - Uncaught exceptions from Flask-Rebar are converted to appropriate HTTP errors.


Example
-------

```python
from flask import Flask
from flask_rebar import errors, Registry
from marshmallow import fields, Schema


from my_app import database


registry = Registry()


class GetTodoSchema(Schema):
    complete = fields.Boolean()


class TodoSchema(Schema):
    id = fields.Integer()
    complete = fields.Boolean()
    description = fields.String()


@registry.handles(
    path='/todos/<int:todo_id>',
    method='GET',
    query_string_schema=UpdateTodoSchema(),
    marshal_schemas=TodoSchema(),
)
def get_todo(todo_id):
    """
    This docstring will be rendered as the operation's description in
    the auto-generated OpenAPI specification.
    """
    if todo_id not in database:
        # Errors are converted to appropriate HTTP errors
        raise errors.NotFound()

    # The query string has already been validated by `query_string_schema`
    complete = framer.validated_args.get('complete')

    ...

    # The response will be marshaled by `marshal_schemas`
    return {'data': {}}


def create_app(name):
    app = Flask(name)
    registry.init_app(app)
    return app


if __name__ == '__main__':
    create_app(__name__).run()
```

For a more complete example, check out the example app at [examples/todo.py](examples/todo.py). Some example requests to this example app can be found at [examples/todo_output.md](examples/todo_output.md).


Documentation
-------------


Installation
------------

```
pip install flask-rebar
```


Similar Packages
----------------

There are number of packages out there that solve a similar problem. Here are just a few:

- [Connexion](https://github.com/zalando/connexion)
- [Flask-RESTful](https://github.com/flask-restful/flask-restful)
- [flask-apispec](https://github.com/jmcarp/flask-apispec)
- [Flasgger](https://github.com/rochacbruno/flasgger)

These are all great projects, and one might work better for your use case. Flask-Rebar solves a similar problem with its own its own twist on the approach.


Philosophy
----------

**OpenAPI as a side effect**

Flask-Rebar aims to free developers from having to think about OpenAPI.

This is not always practical, so some of OpenAPI's needs sneak up to Flask-Rebar. C'est la vie.

Flask-Rebar tries not to constrain a service by what is possible with OpenAPI. This means, for better and for worse, that more complex validation logic than can be represented in an OpenAPI specification.
OpenAPI 3.0 promises to bridge some of this gap, and we have plans to support OpenAPI 3.0 once the tooling catches up (e.g. [swagger-codegen](https://github.com/swagger-api/swagger-codegen).

**Marshmallow, marshmallow, marshmallow**

Marshmallow is a popular tool for validation/marshaling of objects. Flask-Rebar uses Marshmallow for request validation _and_ response marshaling.

Custom Marshmallow schemas/fields should work by default with OpenAPI spec generation, and Marshmallow-to-OpenAPI conversions should be easily extendable to support the trickiest of Marshmallow schemas.

**Opinions are dangerous**

Flask-Rebar shouldn't care about any particular flavor of REST, what database a service might be backed by, how a service authenticates, etc. It should just provide the tools to make common patterns quicker to implement.

There's always an exception (e.g. some endpoint that doesn't return JSON), and Flask-Rebar should be easily bypass-able.


Who's using Flask-Rebar
-----------------------

PlanGrid!


Contribute
----------


License
-------

`flask-rebar` is released under an [MIT License](https://opensource.org/licenses/MIT). See [LICENSE](LICENSE) for details.

> **Copyright &copy; 2018-present PlanGrid, Inc.**
