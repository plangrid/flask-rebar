API Versioning
--------------

URL Prefixing
=============

There are many ways to do API versioning. Flask-Rebar encourages a simple and very common approach - URL prefixing.

.. code-block:: python

   from flask import Flask
   from flask_rebar import Rebar


   rebar = Rebar()
   v1_registry = rebar.create_handler_registry(prefix='/v1')
   v2_registry = rebar.create_handler_registry(prefix='/v2')

   @v1_registry.handles(rule='/foos')
   @v2_registry.handles(rule='/foos')
   def get_foos():
       ...

   @v1_registry.handles(rule='/bar')
   def get_bars():
       ...

   @v2_registry.handles(rule='/bar')
   def get_bars():
       ...

   app = Flask(__name__)
   rebar.init_app(app)

Here we have two registries, and both get registered when calling ``rebar.init_app``.

The same handler function can be used for multiple registries.

This will produce a separate Swagger specification and UI instance per API version, which Flask-Rebar encourages for better support with tools like `swagger-codegen <https://github.com/swagger-api/swagger-codegen>`_.


Cloning a Registry
==================

While its recommended to start versioning an API from the get go, sometimes we don't. In that case, it's a common practice to assume that no version prefix is the same as version 1 of the API in order to maintain backwards compatibility for clients that might already be calling non-prefixed endpoints.

Flask-Rebar supports copying an entire registry and changing the URL prefix:

.. code-block:: python

   from flask import Flask
   from flask_rebar import Rebar


   rebar = Rebar()
   registry = rebar.create_handler_registry()

   @registry.handles(rule='/foos')
   def get_foos():
       ...

   v1_registry = registry.clone()
   v1_registry.prefix = '/v1'
   rebar.add_handler_registry(v1_registry)

   app = Flask(__name__)
   rebar.init_app(app)
