Basics
******

Registering a Handler
=====================

Let's first take a look at a very basic API using Flask-Rebar. For these examples we will use basic
marshmallow Schemas. As of flask-rebar 2.0, we now have support for marshmallow-objects as well,
which we'll describe after the basic examples.

.. code-block:: python

   from flask import Flask
   from flask_rebar import Rebar
   from flask_rebar import ResponseSchema
   from marshmallow import fields


   rebar = Rebar()
   registry = rebar.create_handler_registry()


   class TodoSchema(ResponseSchema):
       id = fields.Integer()


   @registry.handles(
      rule='/todos/<id>',
      method='GET',
      response_body_schema=TodoSchema()  # for versions <= 1.7.0, use marshal_schema
   )
   def get_todo(id):
       ...
       return {'id': id}

   app = Flask(__name__)
   rebar.init_app(app)

   if __name__ == '__main__':
       app.run()

We first create a ``Rebar`` instance. This is a Flask extension and takes care of attaching all the Flask-Rebar goodies to the Flask application.

We then create a handler registry that we will use to declare handlers for the service.

``ResponseSchema`` is an extension of ``marshmallow.Schema`` that throws an error if additional fields not specified in the schema are included in the request parameters. It's usage is optional - a normal Marshmallow schema will also work.

``rule`` is the same as Flask's `rule <http://flask.pocoo.org/docs/latest/api/#url-route-registrations>`_, and is the URL rule for the handler as a string.

``method`` is the HTTP method that the handler will accept. To register multiple methods for a single handler function, decorate the function multiple times.

``response_body_schema`` is a Marshmallow schema that will be used marshal the return value of the function. `marshmallow.Schema.dump <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.dump>`_ will be called on the return value. ``response_body_schema`` can also be a dictionary mapping status codes to Marshmallow schemas - see :ref:`Marshaling`.  *NOTE: In Flask-Rebar 1.0-1.7.0, this was referred to as ``marshal_schema``. It is being renamed and both names will function until version 2.0*

The handler function should accept any arguments specified in ``rule``, just like a Flask view function.

When calling ``Rebar.init_app``, all of the handlers for all the registries created by that rebar instance will be registered with the Flask application.
Each registry will get its own Swagger specification and Swagger UI endpoint. This is intended as one way of doing API versioning - see :ref:`API Versioning` for more info.


Request Body Validation
=======================

.. code-block:: python

   from flask_rebar import RequestSchema


   class CreateTodoSchema(RequestSchema):
       description = fields.String(required=True)


   @registry.handles(
      rule='/todos',
      method='POST',
      request_body_schema=CreateTodoSchema(),
   )
   def create_todo():
       body = rebar.validated_body
       description = body['description']
       . . .


``RequestSchema`` is an extension of ``marshmallow.Schema`` that throws an internal server error if an object is missing a required field. It's usage is optional - a normal Marshmallow schema will also work.

This request schema is passed to ``request_body_schema``, and the handler will now call `marshmallow.Schema.load <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.load>`_ on the request body decoded as JSON. A 400 error with a descriptive error will be returned if validation fails.

The validated parameters are available as a dictionary via the ``rebar.validated_body`` proxy.


Query String Validation
=======================

.. code-block:: python

   class GetTodosSchema(RequestSchema):
       exclude_completed = fields.String(missing=False)


   @registry.handles(
      rule='/todos',
      method='GET',
      query_string_schema=GetTodosSchema(),
   )
   def get_todos():
       args = rebar.validated_args
       exclude_completed = args['exclude_completed']
       . . .


This request schema is passed to ``query_string_schema``, and the handler will now call `marshmallow.Schema.load <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.load>`_ on the query string parameters retrieved from Flask's ``request.args``. A 400 error with a descriptive error will be returned if validation fails.

The validated parameters are available as a dictionary via the ``rebar.validated_args`` proxy.

``request_body_schema`` and ``query_string_schema`` behave very similarly, but keep in mind that query strings can be a bit more limited in the amount of data that can be (or rather, should be) encoded in them, so the schemas for query strings should aim to be simpler.


Header Parameters
=================

.. code-block:: python

   from marshmallow import Schema


   class HeadersSchema(Schema):
       user_id = fields.String(required=True, load_from='X-MyApp-UserId')


   @registry.handles(
      rule='/todos/<id>',
      method='PUT',
      headers_schema=HeadersSchema(),
   )
   def update_todo(id):
       headers = rebar.validated_headers
       user_id = headers['user_id']
       . . .


.. note:: In version 3 of Marshmallow, The `load_from` parameter of fields changes to `data_key`

In this case we use a regular Marshmallow schema, since there will almost certainly be other HTTP headers in the request that we don't want to validate against.

This schema is passed to ``headers_schema``, and the handler will now call `marshmallow.Schema.load <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.load>`_ on the header values retrieved from Flask's ``request.headers``. A 400 error with a descriptive error will be returned if validation fails.

The validated parameters are available as a dictionary via the ``rebar.validated_headers`` proxy.

A schema can be added as the default headers schema for all handlers via the registry:

.. code-block:: python

   registry.set_default_headers_schema(HeadersSchema())

This default can be overriden in any particular handler by setting ``headers_schema`` to something else, including ``None`` to bypass any header validation.


Marshaling
==========

.. note:: In version 2.0, we updated our supported versions of Marshmallow from 2.x to 3.x. One of the more significant changes in Marshmallow is that ``Schema.dump`` does not trigger validation. This can result in significant performance improvements. In Flask-Rebar 2.0, we have made validation of marshalled results *opt-in*.

The ``response_body_schema`` (previously ``marshal_schema``) argument of ``HandlerRegistry.handles`` can be one of three types: a ``marshmallow.Schema``, a dictionary mapping integers to ``marshmallow.Schema``, or ``None``.

In the case of a ``marshmallow.Schema``, that schema is used to ``dump`` the return value of the handler function.

In the case of a dictionary mapping integers to ``marshmallow.Schemas``, the integers are interpreted as status codes, and the handler function must return a tuple of ``(response_body, status_code)``:

.. code-block:: python

   @registry.handles(
      rule='/todos',
      method='POST',
      response_body_schema={
          201: TodoSchema()
      }
   )
   def create_todo():
       ...
       return {'id': id}, 201

The schema to use for marshaling will be retrieved based on the status code the handler function returns. This isn't the prettiest part of Flask-Rebar, but it's done this way to help with the automatic Swagger generation.

In the case of ``None`` (which is also the default), no marshaling takes place, and the return value is passed directly through to Flask. This means the if ``response_body_schema`` is ``None``, the return value must be a return value that Flask supports, e.g. a string or a ``Flask.Response`` object.

.. code-block:: python


   @registry.handles(
      rule='/todos',
      method='GET',
      response_body_schema=None
   )
   def get_todos():
       ...
       return 'Hello World!'

This is a handy escape hatch when handlers don't fit the Swagger/REST mold very well, but it the swagger generation won't know how to describe this handler's response and should be avoided.

Opting In to Response Validation
--------------------------------

There are two ways to opt-in to response validation:

#. Globally, via ``rebar.set_validate_on_dump(bool)``. Using this method, it is easy to turn on validation for things like test cases, while reaping performance gains by leaving it off in your production endpoints (assuming your API contract testing is sufficient to guarantee that your API can't return invalid data).
#. At schema level, via ``flask_rebar.validation.RequireOnDumpMixin`` (including if you use our legacy pre-canned ``ResponseSchema`` as the base class for your schemas). Any schema that includes that mixin is automatically opted in to response validation, regardless of global setting. Note that in Flask-Rebar 2, that mixin serves *only* as a "marker" to trigger validation; we plan to augment/replace this with ability to use `SchemaOpts` as a more logical way of accomplishing the same thing in the near future (https://github.com/plangrid/flask-rebar/issues/252).



Errors
======

Flask-Rebar includes a set of error classes that can be raised to produce HTTP errors.

.. code-block:: python

   from flask_rebar import errors

   @registry.handles(
      rule='/todos/<id>',
      method='GET',
   )
   def get_todo(id):
       if not user_allowed_to_access_todo(
               user_id=rebar.validated_headers['user_id'],
               todo_id=id
       ):
           raise errors.Forbidden(
               msg='User not allowed to access todo object.',
               additional_data={
                   'my_app_internal_error_code': 123
               }
           )
       ...

The ``msg`` parameter will override the "message" key of the JSON response. Furthermore, the JSON response will be updated with ``additional_data``.

Validation errors are raised automatically, and the JSON response will include an ``errors`` key with more specific errors about what in the payload was invalid (this is done with the help of Marshmallow validation).

For most of our predefined errors, as of version 2.0 we include not just a message but also a "rebar-internal" error "code". By default this is included in those responses as ``rebar_error_code`` but you can control that by setting the ``error_code_attr`` attribute on your instance of ``Rebar`` to your preferred name, or to ``None`` to suppress inclusion of rebar-internal error codes entirely.

Support for marshmallow-objects
===============================
New and by request in version 2.0, we include some support for ``marshmallow-objects``!

CAVEAT: We do not have a dependency on ``marshmallow-objects`` outside of ``dev`` extras. If you're developing a flask-rebar app
that depends on ``marshmallow-objects``, be sure to include it in your explicit dependencies, and be aware that ``flask-rebar``
is only tested with 2.3.x versions.

In many cases, you can just use a ``Model`` where you would use a ``Schema``, but there are a couple of things to look out for:

* In many places throughout ``flask-rebar``, when you need to provide a schema (for example, when registering a handler),
  you can pass either your ``Schema`` *class or an instance of it* and rebar does the rest. This is also true of ``Model``;
  however, you can't instantiate a ``Model`` without providing data if there are required fields. We recommend just passing
  relevant ``Model`` subclasses consistently.
* When generating OpenAPI specification, if you use ``marshmallow.Schema`` classes, they are represented in OpenAPI by their
  class name. If you use ``marshmallow_objects.Model`` classes, they are represented as the class name **with a suffix** of "Schema".
  Note that you can use ``__swagger_title__`` to override this and call them whatever you want.
* ``NestedModel`` is supported, but there is not a good way to specify a "title" for OpenAPI generation. If you need to
  provide custom titles for your nested models, use ``flask_rebar.utils.marshmallow_objects_helpers.NestedTitledModel``
