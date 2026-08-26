Pydantic
********

Flask-Rebar can adapt Pydantic v2 models for request validation, response
marshaling, and Swagger generation. Pydantic remains optional, so install the
extra in applications that use it:

.. code-block:: console

   pip install "flask-rebar[pydantic]"

Models
------

Use ``ApiModel`` for API payloads. It validates unknown fields strictly and
supports population by field name.

.. code-block:: python

   from flask_rebar.utils.pydantic import ApiModel


   class CreateWidget(ApiModel):
       name: str
       page_width: float

Use ``CamelCaseApiModel`` instead for APIs that use camelCase. 
It behaves like ``ApiModel`` but also accepts and serializes
camel-case aliases (``pageWidth``) alongside the Python field names:

.. code-block:: python

   from flask_rebar.utils.pydantic import CamelCaseApiModel


   class CreateWidget(CamelCaseApiModel):
       name: str
       page_width: float


Pass the cached Flask-Rebar schema to a handler. ``validated_body`` returns
the Pydantic model that validated the request (compatible with type hints):

.. code-block:: python

   from flask_rebar import Rebar
   from flask_rebar.utils.pydantic import validated_body

   rebar = Rebar()
   registry = rebar.create_handler_registry()


   @registry.handles(
       rule="/widgets",
       method="POST",
       request_body_schema=CreateWidget.rebar_schema(),
       response_body_schema={201: CreateWidget.rebar_schema()},
   )
   def create_widget():
       widget = validated_body(CreateWidget)
       # return a pydantic type too
       return widget, 201


Use ``validated_args`` in the same way with ``query_string_schema``. Repeated
query parameters are preserved for list, set, tuple, and optional sequence
fields.

Headers work the same way, but HTTP header names don't match either
``ApiModel``'s snake_case fields or ``CamelCaseApiModel``'s camelCase
aliases, so give each field an explicit alias for the header it maps to.
Unlike bodies and query strings, unrecognized headers (``Host``,
``User-Agent``, and the rest every real request carries) are always
ignored rather than rejected:

.. code-block:: python

   from pydantic import Field

   from flask_rebar.utils.pydantic import ApiModel, validated_headers


   class WidgetHeaders(ApiModel):
       api_key: str = Field(alias="X-Api-Key")


   @registry.handles(
       rule="/widgets",
       method="POST",
       headers_schema=WidgetHeaders.rebar_schema(),
   )
   def create_widget():
       headers = validated_headers(WidgetHeaders)
       ...

Use the ``DateTime`` annotation for fields that should keep their UTC
offset when serialized to JSON, rather than Pydantic's default:

.. code-block:: python

   from flask_rebar.utils.pydantic import ApiModel, DateTime


   class WidgetResponse(ApiModel):
       updated_at: DateTime

Plain Pydantic models remain supported when the API defaults are not
suitable:

.. code-block:: python

   from pydantic import BaseModel
   from flask_rebar.utils.pydantic import schema_for


   class HealthResponse(BaseModel):
       status: str


   response_schema = schema_for(HealthResponse)


Responses
---------

Pydantic serializes response models, mappings, and objects whose attributes
match the model fields. Mix ``OmitNone`` before ``ApiModel`` (or
``CamelCaseApiModel``) to remove null values from Flask-Rebar responses
without changing ordinary ``model_dump`` behavior:

.. note::

   Unlike a plain Marshmallow schema, whose ``dump`` never validates by
   default, a Pydantic-backed response schema always validates a mapping or
   attribute-bearing object against the model before serializing it (since
   Pydantic has no unvalidated "dump" path for non-model input). A handler
   that returns data missing a required field will raise, even with
   Flask-Rebar's ``validate_on_dump`` left at its default of ``False``.

.. code-block:: python

   from flask_rebar.utils.pydantic import CamelCaseApiModel, OmitNone


   class WidgetResponse(OmitNone, CamelCaseApiModel):
       name: str
       description: str | None = None


Swagger
-------

Importing ``flask_rebar.utils.pydantic`` registers its converters with
Flask-Rebar. ``ApiModel.rebar_schema()`` therefore participates in the normal
request, response, query-string, and header schema paths.

Pydantic emits modern JSON Schema. Flask-Rebar's default Swagger 2 generator
supports ordinary models, while ``SwaggerV3Generator`` preserves Pydantic's
complete OpenAPI 3.1 schema for nullable values, unions, and advanced
constraints.

.. code-block:: python

   from flask_rebar import Rebar, SwaggerV3Generator

   rebar = Rebar()
   registry = rebar.create_handler_registry(
       swagger_generator=SwaggerV3Generator(),
   )
