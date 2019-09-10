Authentication
--------------

Authenticator Interface
=======================

Flask-Rebar has very basic support for authentication - an authenticator just needs to implement ``flask_rebar.authenticators.Authenticator``, which is just a class with an ``authenticate`` method that will be called before a handler function.


Header API Key Authentication
=============================

Flask-Rebar ships with a ``HeaderApiKeyAuthenticator``.

.. code-block:: python

   from flask_rebar import HeaderApiKeyAuthenticator

   authenticator = HeaderApiKeyAuthenticator(header='X-MyApp-ApiKey')

   @registry.handles(
      rule='/todos/<id>',
      method='GET',
      authenticators=authenticator,
   )
   def get_todo(id):
       ...

   authenticator.register_key(key='my-secret-api-key')

   # Probably a good idea to include a second valid value to make key rotation
   # possible without downtime
   authenticator.register_key(key='my-secret-api-key-backup')

The ``X-MyApp-ApiKey`` header must now match ``my-secret-api-key``, or else a ``401`` error will be returned.

This also supports very lightweight way to identify clients based on the value of the api key:

.. code-block:: python

   from flask import g

   authenticator = HeaderApiKeyAuthenticator(header='X-MyApp-ApiKey')

   @registry.handles(
      rule='/todos/<id>',
      method='GET',
      authenticators=authenticator,
   )
   def get_todo(id):
       app_name = authenticator.authenticated_app_name
       if app_name == 'client_1':
            raise errors.Forbidden()
       ...

   authenticator.register_key(key='key1', app_name='client_1')
   authenticator.register_key(key='key2', app_name='client_2')

This is meant to differentiate between a small set of client applications, and will not scale to a large set of keys and/or applications.

An authenticator can be added as the default headers schema for all handlers via the registry:

.. code-block:: python

   registry.set_default_authenticator(authenticator)

This default can be extended for any particular handler by passing flask_rebar.authenticators.USE_DEFAULT as one of the authenticators.
This default can be overriden in any particular handler by setting ``authenticators`` to something else, including ``None`` to bypass any authentication.

This Header API Key authentication mechanism was designed to work for services behind some sort of reverse proxy that is handling the harder bits of client authentication.

Extensions for Authentication
=============================
For situations that require something more robust than the basic header-based authentication, Flask-Rebar can be extended.  For example, see the following  open-source Flask-Rebar extension(s):

* `Flask-Rebar-Auth0 <https://github.com/Sytten/flask-rebar-auth0>`_ - `Auth0 <https://auth0.com/>`_ authenticator for Flask-Rebar
