.. Flask-Rebar documentation master file, created by
   sphinx-quickstart on Thu Feb 22 16:45:26 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flask-Rebar
======================

Welcome to Flask-Rebar's documentation!

Flask-Rebar combines `flask <http://flask.pocoo.org/>`_, `marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_, and `swagger <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md>`_ for robust REST services.


Features
--------

* **Request and Response Validation** - Flask-Rebar relies on schemas from the popular Marshmallow package to validate incoming requests and marshal outgoing responses.
* **Automatic Swagger Generation** - The same schemas used for validation and marshaling are used to automatically generate OpenAPI specifications (a.k.a. Swagger). This also means automatic documentation via `Swagger UI <https://swagger.io/swagger-ui/>`_.
* **Error Handling** - Uncaught exceptions from Flask-Rebar are converted to appropriate HTTP errors.


Example
-------

Here's what a basic Flask-Rebar application looks like:

.. code-block:: python

   from flask import Flask
   from flask_rebar import errors, Rebar
   from marshmallow import fields, Schema

   from my_app import database


   rebar = Rebar()

   # All handler URL rules will be prefixed by '/v1'
   registry = rebar.create_handler_registry(prefix='/v1')

   class TodoSchema(Schema):
       id = fields.Integer()
       complete = fields.Boolean()
       description = fields.String()

   # This schema will validate the incoming request's query string
   class GetTodosQueryStringSchema(Schema):
       complete = fields.Boolean()

   # This schema will marshal the outgoing response
   class GetTodosResponseSchema(Schema):
       data = fields.Nested(TodoSchema, many=True)


   @registry.handles(
       rule='/todos',
       method='GET',
       query_string_schema=GetTodosQueryStringSchema(),
       response_body_schema=GetTodosResponseSchema(), # For version <= 1.7.0 use marshal_schema
   )
   def get_todos():
       """
       This docstring will be rendered as the operation's description in
       the auto-generated OpenAPI specification.
       """
       # The query string has already been validated by `query_string_schema`
       complete = rebar.validated_args.get('complete')

       ...

       # Errors are converted to appropriate HTTP errors
       raise errors.Forbidden()

       ...

       # The response will be marshaled by `marshal_schema`
       return {'data': []}


   def create_app(name):
       app = Flask(name)
       rebar.init_app(app)
       return app


   if __name__ == '__main__':
       create_app(__name__).run()


.. toctree::
   :maxdepth: 2
   :caption: Guide:

   why
   quickstart/installation
   quickstart/basics
   quickstart/api_versioning
   quickstart/swagger_generation
   quickstart/authentication
   api_reference
   tutorials
   recipes
   contributing
   version_history
   changelog
