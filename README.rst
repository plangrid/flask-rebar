Flask-Rebar
===========

.. image:: https://readthedocs.org/projects/flask-rebar/badge/?version=latest
   :target: http://flask-rebar.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

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


Why Flask-Rebar?
----------------

There are number of packages out there that solve a similar problem. Here are just a few:

* `Connexion <https://github.com/zalando/connexion>`_
* `Flask-RESTful <https://github.com/flask-restful/flask-restful>`_
* `flask-apispec <https://github.com/jmcarp/flask-apispec>`_
* `Flasgger <https://github.com/rochacbruno/flasgger>`_

These are all great projects, and one might work better for your use case. Flask-Rebar solves a similar problem with its own its own twist on the approach:

Marshmallow for validation *and* marshaling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some approaches use Marshmallow only for marshaling, and provide a secondary schema module for request validation.

Flask-Rebar is Marshmallow first. Marshmallow is a well developed, well supported package, and Flask-Rebar is built on top of it from the get go.


Swagger as a side effect
~~~~~~~~~~~~~~~~~~~~~~~~

Some approaches generate code *from* a Swagger specification, or generate Swagger from docstrings. Flask-Rebar aims to make Swagger (a.k.a. OpenAPI) a byproduct of writing application code with Marshmallow and Flask.

This is really nice if you prefer the rich validation/transformation functionality of Marshmallow over Swagger's limited.

It also alleviates the need to manually keep an API's documentation in sync with the actual application code - the schemas used by the application are the same schemas used to generate Swagger.

It's also not always practical - Flask-Rebar sometimes has to expose some Swagger specific things in its interface. C'est la vie.

And since Marshmallow can be more powerful than Swagger, it also means its possible to have validation logic that can't be represented in Swagger. Flask-Rebar assumes this is inevitable, and assumes that it's OK for an API to raise a 400 error that Swagger wasn't expecting.


Contributing
------------

There is still work to be done, and contributions are encouraged! Check out the `contribution guide <CONTRIBUTING.rst>`_ for more information.
