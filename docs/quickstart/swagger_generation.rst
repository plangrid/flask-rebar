Swagger Generation
------------------

Swagger Endpoints
=================

Flask-Rebar aims to make Swagger generation and documentation a side effect of building the API. The same Marshmallow schemas used to actually validate and marshal in the live API are used to generate a Swagger specification, which can be used to generate API documentation and client libraries in many languages.

Flask-Rebar adds two additional endpoints for every handler registry:

- ``/<registry prefix>/swagger``
- ``/<registry prefix>/swagger/ui``

``/swagger`` and ``/swagger/ui`` are configurable:

.. code-block:: python

   registry = rebar.create_handler_registry(
       swagger_path='/apidocs',
       swagger_ui_path='/apidocs-ui'
   )

The HTML documentation is generated with `Swagger UI <https://swagger.io/swagger-ui/>`_.


Swagger Version
===============

Flask-Rebar supports both Swagger v2 and Swagger v3 (synonymous with OpenAPI v2 and OpenAPI v3, respectively).

For backwards compatibility, handler registries will generate Swagger v2 by default. To have the registries generate Swagger v3 instead, specify an instance ``SwaggerV3Generator`` when instantiating the registry:

.. code-block:: python

   from flask_rebar import SwaggerV3Generator

   registry = rebar.create_handler_registry(
       swagger_generator=SwaggerV3Generator()
   )

Serverless Generation
=====================

It is possible to generate the Swagger specification without running the application by using ``SwaggerV2Generator`` or ``SwaggerV3Generator`` directly. This is helpful for generating static Swagger specifications.

.. code-block:: python

   from flask_rebar import SwaggerV3Generator
   from flask_rebar import Rebar

   rebar = Rebar()
   registry = rebar.create_handler_registry()

   # ...
   # register handlers and what not

   generator = SwaggerV3Generator()
   swagger = generator.generate(registry)

Extending Swagger Generation
============================

Flask-Rebar does its very best to free developers from having to think about how their applications map to Swagger, but sometimes it needs some hints.

``flask_rebar.swagger_generation.SwaggerV2Generator`` is responsible for converting a registry to a Swagger specification.

operationId
^^^^^^^^^^^

All Swagger operations (i.e. a combination of a URL route and method) can have an "operationId", which is name that is unique to the specification. This operationId is very useful for code generation tools, e.g. swagger-codegen, that use the operationId to generate method names.

The generator first checks for the value of ``endpoint`` specified when declaring the handler with a handler registry. If this is not included, the generator defaults to the name of the function.

In many cases, the name of the function will be good enough. If you need more control over the operationId, specific an ``endpoint`` value.

summary
^^^^^^^^^^^

Swagger operations can have summaries. If a handler function has a docstring, the generator will use the content before the first blank line if any as the summary.


description
^^^^^^^^^^^

Swagger operations can have descriptions. If a handler function has a docstring with a blankline the generator will the texts after it as the description.

definition names
^^^^^^^^^^^^^^^^

The generator makes use of Swagger "definitions" when representing schemas in the specification.

The generator first checks for a ``__swagger_title__`` on Marshmallow schemas when determining a name for its Swagger definition. If this is not specified, the generator defaults to the name of the schema's class.

Custom Marshmallow types
^^^^^^^^^^^^^^^^^^^^^^^^

The generator knows how to convert most built in Marshmallow types to their corresponding Swagger representations, and it checks for the appropriate converter by iterating through a schema/field/validator's method resolution order, so simple extensions of Marshmallow fields should work out of the box.

If a field the extends Marshmallow's abstract field, or want to a particular Marshmallow type to have a more specific Swagger definition, you can add a customer converter.

Here's an example of a custom converter for a custom Marshmallow converter:

.. code-block:: python

   import base64

   from flask_rebar.swagger_generation import swagger_words
   from flask_rebar.swagger_generation.marshmallow_to_swagger import sets_swagger_attr
   from flask_rebar.swagger_generation.marshmallow_to_swagger import request_body_converter_registry
   from flask_rebar.swagger_generation.marshmallow_to_swagger import StringConverter
   from marshmallow import fields, ValidationError


   class Base64EncodedString(fields.String):
        def _serialize(self, value, attr, obj):
            return base64.b64encode(value).encode('utf-8')

        def _deserialize(self, value, attr, data):
            try:
                return base64.b64decode(value.decode('utf-8'))
            except UnicodeDecodeError:
                raise ValidationError()


   class Base64EncodedStringConverter(StringConverter):
       @sets_swagger_attr(swagger_words.format)
       def get_format(self, obj, context):
           return swagger_words.byte

   request_body_converter_registry.register_type(Base64EncodedStringConverter())


First we've defined a ``Base64EncodedString`` that handles serializing/deserializing a string to/from base64. We want this field to be represented more specifically in our Swagger spec with a "byte" format.

We extend the ``StringConverter``, which handles setting the "type".

Methods on the new converter class can be decorated with ``sets_swagger_attr``, which accepts a single argument for which attribute on the JSON document to set with the result of the method.

The method should take two arguments in addition to ``self``: ``obj`` and ``context``.
``obj`` is the current Marshmallow object being converted. In the above case, it will be an instance of ``Base64EncodedString``.
``context`` is a namedtuple that holds some helpful information for more complex conversions:

* ``convert`` - This will hold a reference to a convert method that can be used to make recursive calls
* ``memo`` - This holds the JSONSchema object that's been converted so far. This helps convert Validators, which might depend on the type of the object they are validating.
* ``schema`` - This is the full schema being converted (as opposed to ``obj``, which might be a specific field in the schema).
* ``openapi_version`` - This is the major version of OpenAPI being converter for

We then add an instance of the new converter to the ``request_body_converter_registry``, meaning this field will only be valid for request bodies. We can add it to multiple converter registries or choose to omit it from some if we don't think a particular type of field should be valid in certain situations (e.g. the query_string_converter_registry doesn't support ``Nested`` fields).

Default response
^^^^^^^^^^^^^^^^

Another really tricky bit of the Swagger specification to automatically generate is the default response to operations. The generator needs a little hand-holding to get this right, and accepts a ``default_response_schema``. By default this is set to a schema for the default error handling response.

To customize it:

.. code-block:: python

   from marshmallow import Schema, fields
   from flask_rebar import SwaggerV2Generator
   from flask_rebar import Rebar

   class DefaultResponseSchema(Schema):
       text = fields.String()

   generator = SwaggerV2Generator(
       default_response_schema=DefaultResponseSchema()
   )

   rebar = Rebar()
   registry = rebar.create_handler_registry(swagger_generator=generator)

Notice that since we've started to customize the swagger generator, we should specify the generator instance when instantiating our Registry instance so our swagger endpoints get this same default response.

Authenticators
^^^^^^^^^^^^^^

We also need to tell the generator how to represent custom Authenticators as Swagger.

.. code-block:: python

   from flask_rebar.authenticators import Authenticator
   from flask_rebar import SwaggerV2Generator
   from flask_rebar import Rebar

   class EasyGoingAuthenticator(Authenticator):
       def authenticate(self):
           pass

   def convert_easy_going_authenticator(authenticator):
       return {
           sw.name: 'easy_going'
           ...
       }

   generator = SwaggerV2Generator()
   generator.register_authenticator_converter(
       authenticator_class=EasyGoingAuthenticator,
       converter=convert_easy_going_authenticator
   )

   rebar = Rebar()
   registry = rebar.create_handler_registry(swagger_generator=generator)

The converter function should take an instance of the authenticator as a single positional argument and return a dictionary representing the `security schema object <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md#securitySchemeObject>`_.

Tags
^^^^

Swagger supports tagging operations with arbitrary strings, and then optionally including additional metadata about those tags at the root Swagger Object.

Handlers can be tagged, which will translate to tags on the Operation Object:

.. code-block:: python

   @registry.handles(
      rule='/todos',
      method='GET',
      tags=['beta']
   )
   def get_todos():
       ...

Optionally, to include additional metadata about tags, pass the metadata directly to the swagger generator:

.. code-block:: python

   from flask_rebar import Tag

   generator = SwaggerV2Generator(
       tags=[
           Tag(
               name='beta',
               description='These operations are still in beta!'
           )
       ]
   )

Servers
~~~~~~~

OpenAPI 3+ replaces "host" with `servers <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#serverObject>`_.

Servers can be specified by creating ``Server`` instances and passing them to the generator:

.. code-block:: python

   from flask_rebar import Server, ServerVariable

   generator = SwaggerV3Generator(
       servers=[
           Server(
               url="https://{username}.gigantic-server.com:{port}/{basePath}",
               description="The production API server",
               variables={
                   "username": ServerVariable(
                       default="demo",
                       description="this value is assigned by the service provider, in this example `gigantic-server.com`",
                   ),
                   "port": ServerVariable(default="8443", enum=["8443", "443"]),
                   "basePath": ServerVariable(default="v2"),
               },
           )
       ]
   )
