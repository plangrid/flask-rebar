API Reference
=============

This part of the documentation covers most of the interfaces for Flask-Rebar.


Rebar Extension
---------------

.. autoclass:: flask_rebar.Rebar
   :members:


Handler Registry
----------------

.. autoclass:: flask_rebar.HandlerRegistry
   :members:


Authenticator Objects
---------------------

.. autoclass:: flask_rebar.authenticators.Authenticator
   :members:

.. autoclass:: flask_rebar.HeaderApiKeyAuthenticator
   :members:


Swagger V2 Generation
---------------------

.. autoclass:: flask_rebar.SwaggerV2Generator
   :members:

.. autofunction:: flask_rebar.swagger_generation.sets_swagger_attr

.. autoclass:: flask_rebar.swagger_generation.ConverterRegistry
   :members:


Helpers
-------

.. autoclass:: flask_rebar.ResponseSchema
.. autoclass:: flask_rebar.RequestSchema
.. autofunction:: flask_rebar.get_validated_args
.. autofunction:: flask_rebar.get_validated_body
.. autofunction:: flask_rebar.marshal
.. autofunction:: flask_rebar.response


Exceptions
----------

.. autoclass:: flask_rebar.errors.HttpJsonError
   :members:

.. autoclass:: flask_rebar.errors.BadRequest

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.Unauthorized

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.PaymentRequired

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.Forbidden

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.NotFound

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.MethodNotAllowed

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.NotAcceptable

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.ProxyAuthenticationRequired

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.RequestTimeout

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.Conflict

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.Gone

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.LengthRequired

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.PreconditionFailed

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.RequestEntityTooLarge

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.RequestUriTooLong

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.UnsupportedMediaType

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.RequestedRangeNotSatisfiable

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.ExpectationFailed

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.UnprocessableEntity

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.InternalError

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.NotImplemented

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.BadGateway

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.ServiceUnavailable

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message

.. autoclass:: flask_rebar.errors.GatewayTimeout

   .. autoattribute:: http_status_code
   .. autoattribute:: default_message
