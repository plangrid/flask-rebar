Pydantic
********

Flask-Rebar can adapt Pydantic v2 models for request validation, response
marshaling, and Swagger generation. Pydantic remains optional, so install the
extra in applications that use it:

.. code-block:: console

   pip install "flask-rebar[pydantic]"

Models
------

Although you can use a plain Pydantic ``BaseModel`` subclass, Flask-Rebar provides two thin subclasses:

- ``ApiModel``, with:
     - ``extra="forbid"``: unknown fields fail validation instead of being ignored,
     - ``from_attributes=True``: instantiate by attribute or by keys,
     - ``populate_by_name=True``: construct instances by field name even when a field has a wire-format alias.
- ``CamelCaseApiModel``,
     - ``alias_generator=to_camel``, automatically generate camel-case aliases for all fields.

.. code-block:: python

   from flask_rebar.utils.pydantic_schema import ApiModel


   class CreateWidget(ApiModel):
       name: str
       page_width: float

Use ``CamelCaseApiModel`` instead for APIs that use camelCase. 
It behaves like ``ApiModel`` but also accepts and serializes
camel-case aliases (``pageWidth``) alongside the Python field names:

.. code-block:: python

   from flask_rebar.utils.pydantic_schema import CamelCaseApiModel


   class CreateWidget(CamelCaseApiModel):
       name: str
       page_width: float


Pass the model class straight to a handler; Flask-Rebar detects Pydantic
models automatically and adapts them, the same way it already does for
plain Marshmallow schema classes. ``validated_body`` returns the Pydantic
model that validated the request (compatible with type hints):

.. code-block:: python

   from flask_rebar import Rebar
   from flask_rebar.utils.pydantic_schema import validated_body

   rebar = Rebar()
   registry = rebar.create_handler_registry()


   @registry.handles(
       rule="/widgets",
       method="POST",
       request_body_schema=CreateWidget,
       response_body_schema={201: CreateWidget},
   )
   def create_widget():
       widget = validated_body(CreateWidget)
       # return a pydantic type too
       return widget, 201


Use ``validated_args`` in the same way with ``query_string_schema``. Repeated
query parameters are preserved for list, set, tuple, and optional sequence
fields.

.. warning:: Avoid ``ApiModel``/``CamelCaseApiModel`` for
    ``query_string_schema``. Real clients routinely attach query parameters,
    and ``extra="forbid"`` would reject these requests with a 400. Define a
    plain ``BaseModel`` with ``extra="ignore"`` for query strings instead.

.. code-block:: python

    from pydantic import BaseModel, ConfigDict


    class ListWidgets(BaseModel):
         model_config = ConfigDict(extra="ignore")

         limit: int = 20

Headers work the same way, but HTTP header names don't match either
``ApiModel``'s snake_case fields or ``CamelCaseApiModel``'s camelCase
aliases, so give each field an explicit alias for the header it maps to.
Unlike bodies and query strings, unrecognized headers (``Host``,
``User-Agent``, and the rest every real request carries) are always
ignored rather than rejected:

.. code-block:: python

   from pydantic import Field

   from flask_rebar.utils.pydantic_schema import ApiModel, validated_headers


   class WidgetHeaders(ApiModel):
       api_key: str = Field(alias="X-Api-Key")


   @registry.handles(
       rule="/widgets",
       method="POST",
       headers_schema=WidgetHeaders,
   )
   def create_widget():
       headers = validated_headers(WidgetHeaders)
       ...

Use the ``DateTime`` annotation for fields that should keep their UTC
offset when serialized to JSON, rather than Pydantic's default:

.. code-block:: python

   from flask_rebar.utils.pydantic_schema import ApiModel, DateTime


   class WidgetResponse(ApiModel):
       updated_at: DateTime



Responses
---------

Pydantic serializes response models, mappings, and objects whose attributes
match the model fields. Mix ``OmitNone`` before ``ApiModel`` (or
``CamelCaseApiModel``) to remove null values from Flask-Rebar responses
without changing ordinary ``model_dump`` behavior:

.. note::

   Unlike a plain Marshmallow schema, whose ``dump`` doesn't validate by
   default, a Pydantic-backed response schema always validates a mapping or 
   object against the model before serializing it . A handler
   that returns data missing a required field will raise, even with
   Flask-Rebar's ``validate_on_dump`` left at its default of ``False``.

.. code-block:: python

   from flask_rebar.utils.pydantic_schema import CamelCaseApiModel, OmitNone


   class WidgetResponse(OmitNone, CamelCaseApiModel):
       name: str
       description: str | None = None

There are two ways to validate or serialize a JSON array of ``Model``
instances. Define a plain Pydantic ``RootModel[list[Model]]`` and pass it
directly to the handler:

.. code-block:: python

    from pydantic import RootModel

    from flask_rebar.utils.pydantic_schema import validated_body


   class WidgetResponses(RootModel[list[WidgetResponse]]):
       pass

   class WidgetRequests(RootModel[list[WidgetRequest]]):
       pass


   @registry.handles(
       rule="/widgets",
       method="POST",
       request_body_schema=WidgetRequests,
       response_body_schema={200: WidgetResponses},
   )
    def list_widgets() -> tuple[list[WidgetResponse], int]:
       widgets: list[WidgetRequest] = validated_body(WidgetRequests).root
       return [w.to_response() for w in widgets], 200

Alternatively, use ``schema_for(Model, many=True)`` when you want to reuse the
same model/class for singular and plural responses. Pass the result in place
of the model class. When this schema is used for request validation, pass the
singular model to ``validated_body``; the ``many=True`` adapter returns a list
of validated model instances:

.. code-block:: python

    from flask_rebar.utils.pydantic_schema import schema_for, validated_body


   @registry.handles(
       rule="/widgets",
       method="POST",
       request_body_schema=schema_for(WidgetRequest, many=True),
       response_body_schema={200: schema_for(WidgetResponse, many=True)},
   )
   def list_widgets() -> tuple[list[WidgetResponse], int]:
       widgets: list[WidgetRequest] = validated_body(WidgetRequest)
       return [w.to_response() for w in widgets], 200


Swagger
-------

Pydantic models do not emit valid Swagger 2 schemas. Flask-Rebar warns the first
time a Pydantic-backed schema is converted through a Swagger 2 generator, but it
does not fail automatically, so the generated Swagger 2 document may still only
fail later when it is validated or used to generate a client.

Use ``SwaggerV3Generator`` with Pydantic models. It generates an OpenAPI 3
document that can represent Pydantic's schema, including nullable values,
unions, and advanced constraints.

.. code-block:: python

   from flask_rebar import Rebar, SwaggerV3Generator

   rebar = Rebar()
   registry = rebar.create_handler_registry(
       swagger_generator=SwaggerV3Generator(),
   )
