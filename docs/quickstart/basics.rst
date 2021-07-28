Basics
------

Registering a Handler
=====================

Let's first take a look at a very basic API using Flask-Rebar. For these examples we will use basic
marshmallow Schemas. As of flask-rebar 2.0, we now have support for marshmallow-objects as well,
which we'll describe after the basic examples.

.. code-block:: python

   # todos.py

   from flask import Flask
   from flask_rebar import Rebar
   from marshmallow import Schema, fields


   rebar = Rebar()
   registry = rebar.create_handler_registry()


   class TodoSchema(Schema):
       # The task we have to do.
       description = fields.String(required=True)

       # The unique id for this Todo. Determined by whatever database we're using.
       id = fields.Integer(
           # We'll explain the dump_only=True shortly.
           dump_only=True
       )


   @registry.handles(
      rule='/todos/<int:id>',
      method='GET',
      # Marshal bodies of 200 (default) responses using the TodoSchema.
      response_body_schema=TodoSchema()
   )
   def get_todo(id):
       todo = _get_todo_or_404(id)  # Some helper function that queries our database.
       # If we got here, it means we were able to find a Todo with the given id.
       # As with Flask, a 200 response code is assumed when we don't say otherwise.
       # Return a dictionary with the data for this Todo, which Rebar will marshal
       # into the response body using our TodoSchema, as we specified above.
       return {'id': todo.id, 'description': todo.description}

   app = Flask(__name__)
   rebar.init_app(app)


Now run your Flask app `as usual <https://flask.palletsprojects.com/en/1.1.x/quickstart/>`__,
e.g.:

.. code-block:: bash

   export FLASK_APP=todos.py
   flask run


We first create a ``Rebar`` instance. This is a Flask extension and takes care of attaching all the Flask-Rebar goodies to the Flask application.

We then create a handler registry that we will use to declare handlers for the service.

``rule`` is the same as Flask's `rule <http://flask.pocoo.org/docs/latest/api/#url-route-registrations>`_, and is the URL rule for the handler as a string.

``method`` is the HTTP method that the handler will accept. To register multiple methods for a single handler function, decorate the function multiple times.

``response_body_schema`` is a Marshmallow schema that will be used to marshal the return value of the function for 200 responses, which (as with Flask) is the default response code when we don't say otherwise. `marshmallow.Schema.dump <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.dump>`_ will be called on the return value to marshal it. ``response_body_schema`` can also be a dictionary mapping different status codes to Marshmallow schemas - see :ref:`Marshaling`.  *NOTE: In Flask-Rebar 1.0-1.7.0, this was referred to as ``marshal_schema``. It is being renamed and both names will function until version 2.0*

The handler function should accept any arguments specified in ``rule``, just like a Flask view function.

When calling ``Rebar.init_app``, all of the handlers for all the registries created by that rebar instance will be registered with the Flask application.
Each registry will get its own Swagger specification and Swagger UI endpoint. This is intended as one way of doing API versioning - see :ref:`API Versioning` for more info.


Request Body Validation
=======================

.. code-block:: python

   @registry.handles(
      rule='/todos/',
      method='POST',
      request_body_schema=TodoSchema(),
      response_body_schema={201: TodoSchema()}
   )
   def create_todo():
       # If we got here, it means we have valid Todo data in the request body.
       # Thanks to specifying the request_body_schema above, Rebar takes care
       # of sending nice 400 responses (with human- and machine-friendly bodies)
       # in response to invalid request data for us.
       description = rebar.validated_body['description']
       new_todo = _insert_todo(description)  # Insert a Todo in our db and return it.
       # We'll want to return a 201 Created response with a Location header, so calculate
       # the url of the new Todo. We use flask.url_for rather than hard-coding this so
       # that if we change the get_todo endpoint's url rule in the future, the url here
       # will stay up-to-date.
       new_todo_url = flask.url_for(
           f'{registry.prefix}.{get_todo.__name__}',
           id=new_todo.id
       )
       response_data = {"id": new_todo.id, "description": new_todo.description}
       return (response_data, 201, {"Location": new_todo_url})


This request schema is passed to ``request_body_schema``, and the handler will now call `marshmallow.Schema.load <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.load>`_ on the request body decoded as JSON. A 400 error with a descriptive error will be returned if validation fails.

The validated parameters are available as a dictionary via the ``rebar.validated_body`` proxy.

Remember when we passed ``dump_only=True`` when defining ``TodoSchema``'s ``id`` field above?
This lets us ignore the ``id`` field when unmarshaling (loading) data,
and only look at it when marshaling (dumping) data.
This allows this schema to be used not just to marshal response bodies,
but also to unmarshal request bodies, where the request either won't know the id
ahead of time, as when creating a new Todo, or otherwise where the id is specified
in the URL path rather than in the body, as when updating a Todo (see below).


Query String Validation
=======================

.. code-block:: python

   class ExcludeCompletedSchema(Schema):
       exclude_completed = fields.String(
           # When this param is not provided, use False as its default value.
           missing=False
       )


   @registry.handles(
      rule='/todos/',
      method='GET',
      query_string_schema=ExcludeCompletedSchema(),
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

   class UserIdSchema(Schema):
       user_id = fields.String(required=True, load_from='X-MyApp-UserId')


   @registry.handles(
      rule='/todos/<int:id>',
      method='PUT',
      request_body_schema=TodoSchema(),
      response_body_schema={204: None},
      # Assume we can trust a special header to contain the authenticated user (e.g.
      # it can only have been set by a gateway that rejects unauthenticated requests).
      headers_schema=UserIdSchema(),
   )
   def update_todo(id):
       user_id = rebar.validated_headers['user_id']
       # Make sure this user is authorized to update this Todo.
       _authorized_or_403(user_id, ...)
       _update_todo(id, rebar.validated_body['description'])  # Update our database.
       # Return a 204 No Content response to indicate operation completed successfully
       # and we have no additional data to return.
       return None, 204



.. note:: This example assumes Marshmallow v2. In version 3 of Marshmallow, The `load_from` parameter of fields changes to `data_key`.

This schema is passed to ``headers_schema``, and the handler will now call `marshmallow.Schema.load <http://marshmallow.readthedocs.io/en/latest/api_reference.html#marshmallow.Schema.load>`_ on the header values retrieved from Flask's ``request.headers``. A 400 error with a descriptive error will be returned if validation fails.

The validated parameters are available as a dictionary via the ``rebar.validated_headers`` proxy.

A schema can be added as the default headers schema for all handlers via the registry:

.. code-block:: python

   registry.set_default_headers_schema(HeadersSchema())

This default can be overriden in any particular handler by setting ``headers_schema`` to something else, including ``None`` to bypass any header validation.


Marshaling
==========

The ``response_body_schema`` argument of ``HandlerRegistry.handles`` can be one of three types: a ``marshmallow.Schema``, a dictionary mapping integers to ``marshmallow.Schema``, or ``None``.

In the case of a ``marshmallow.Schema``, that schema is used to ``dump`` the return value of the handler function for 200 responses.

In the case of a dictionary mapping integers to ``marshmallow.Schemas``, the integers are interpreted as status codes, and the handler function must return a tuple like ``(response_body, status_code)``
(or like ``(response_body, status_code, headers)`` to also include custom headers),
as in the example ``create_todo`` handler function above.
The Schema in the dictionary corresponding to the returned status code will be used to marshal the response.
So ``response_body_schema=Foo()`` is just shorthand for ``response_body_schema={200: Foo()}``.

A status code in the dictionary may also map to ``None``, in which case Rebar will pass whatever value was returned in the body for this status code straight through to Flask. Note, the value must be a return value that Flask supports, e.g. a string, dictionary (as of Flask 1.1.0), or a ``Flask.Response`` object.

Finally, ``response_body_schema`` may be ``None``, which is the default, and works just like ``{200: None}``.

.. code-block:: python


   @registry.handles(
      rule='/foo',
      method='GET',
      response_body_schema=None
   )
   def foo():
       ...
       return 'This string gets returned directly without marshaling'

This is a handy escape hatch when handlers don't fit the Swagger/REST mold very well, but it the swagger generation won't know how to describe this handler's response and should be avoided.


Errors
======

Flask-Rebar includes a set of error classes that can be raised to produce HTTP errors.

.. code-block:: python

   from flask_rebar import errors

   @registry.handles(
      rule='/todos/<int:id>',
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
                   'error_code': 123
               }
           )
       ...

The ``msg`` parameter will override the "message" key of the JSON response. Furthermore, the JSON response will be updated with ``additional_data``.

Validation errors are raised automatically, and the JSON response will include an ``errors`` key with more specific errors about what in the payload was invalid (this is done with the help of Marshmallow validation).

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
