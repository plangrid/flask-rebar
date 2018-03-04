Flask-Rebar
===========

.. image:: https://readthedocs.org/projects/flask-rebar/badge/?version=latest
   :target: http://flask-rebar.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/plangrid/flask-rebar.svg?branch=master
   :target: https://travis-ci.org/plangrid/flask-rebar
   :alt: CI Status

.. image:: https://badge.fury.io/py/flask-rebar.svg
   :target: https://badge.fury.io/py/flask-rebar
   :alt: PyPI status

|

Flask-Rebar combines `flask <http://flask.pocoo.org/>`_, `marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_, and `swagger <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md>`_ for robust REST services.


Features
--------

* **Request and Response Validation** - Flask-Rebar relies on schemas from the popular Marshmallow package to validate incoming requests and marshal outgoing responses.
* **Automatic Swagger Generation** - The same schemas used for validation and marshaling are used to automatically generate OpenAPI specifications (a.k.a. Swagger). This also means automatic documentation via `Swagger UI <https://swagger.io/swagger-ui/>`_.
* **Error Handling** - Uncaught exceptions from Flask-Rebar are converted to appropriate HTTP errors.


Example
-------

.. code-block:: python

   from flask import Flask
   from flask_rebar import errors, Rebar
   from marshmallow import fields, Schema

   from my_app import database


   rebar = Rebar()

   # All handler URL rules will be prefixed by '/v1'
   registry = rebar.create_handler_registry(prefix='/v1')


   # This schema will validate the incoming request's query string
   class GetTodoSchema(Schema):
       complete = fields.Boolean()

   # This schema will marshal the outgoing response
   class TodoSchema(Schema):
       id = fields.Integer()
       complete = fields.Boolean()
       description = fields.String()


   @registry.handles(
       rule='/todos/<int:todo_id>',
       method='GET',
       query_string_schema=UpdateTodoSchema(),
       marshal_schema=TodoSchema(),
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

       # The response will be marshaled by `marshal_schema`
       return {'data': {}}


   def create_app(name):
       app = Flask(name)
       rebar.init_app(app)
       return app


   if __name__ == '__main__':
       create_app(__name__).run()


For a more complete example, check out the example app at `examples/todo.py <examples/todo/todo.py>`_. Some example requests to this example app can be found at `examples/todo_output.md <examples/todo/todo_output.md>`_.


Installation
------------

.. code-block::

   pip install flask-rebar


Documentation
-------------

More extensive documentation can be found  `here <https://flask-rebar.readthedocs.io>`_.


Contributing
------------

There is still work to be done, and contributions are encouraged! Check out the `contribution guide <CONTRIBUTING.rst>`_ for more information.
