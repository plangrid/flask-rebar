Recipes
-------

Class Based Views
=================

Some people prefer basing Flask view functions on classes rather than functions, and other REST frameworks for Flask base themselves on classes.

First, an opinion: people often prefer classes simply because they are used to them. If you're looking for classes because functions make you uncomfortable, I encourage you to take a moment to reconsider your feelings. Embracing functions, `thread locals <http://flask.pocoo.org/docs/1.0/design/#thread-locals>`_, and all of Flask's little quirks can feel oh so good.

With that, there are perfectly valid use cases for class based views, like creating abstract views that can be inherited and customized. This is the main intent of Flask's built-in `pluggable views <http://flask.pocoo.org/docs/latest/views/>`_.

Here is a simple recipe for using Flask-Rebar with these pluggable views:


.. code-block:: python

   from flask import Flask
   from flask import request
   from flask.views import MethodView
   from flask_rebar import Rebar


   rebar = Rebar()
   registry = rebar.create_handler_registry()


   class AbstractResource(MethodView):
       def __init__(self, database):
           self.database = database

       def get_resource(self, id):
           raise NotImplemented

       def get(self, id):
           return self.get_resource(id)

       def put(self, id):
           resource = self.get_resource(id)
           resource.update(rebar.validated_body)
           return resource


   class Todo(AbstractResource):
       def get_resource(self, id):
           return get_todo(database, id)


   for method, request_body_schema in [
       ("get", None),
       ("put", UpdateTodoSchema()),
   ]:
       registry.add_handler(
           func=Todo.as_view(method + "_todo", database=database),
           rule="/todos/<id>",
           response_body_schema=TodoSchema(),  # for versions <= 1.7.0, use marshal_schema
           method=method,
           request_body_schema=request_body_schema,
       )


This isn't a super slick, classed based interface for Flask-Rebar, but it *is* a way to use unadulterated Flask views to their full intent with minimal `DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_ violations.


Combining Security/Authentication
=================================

Authentication is hard, and complicated. Flask-Rebar supports custom Authenticator classes so that you can make
your authentication as complicated as your heart desires.

Sometime though you want to combine security requirements.
Maybe an endpoint should allow either an admin user or a user with an "edit" permission,
maybe you want to allow requests to use Auth0 or an Api Key,
maybe you want to only authenticate if it's Sunday and Jupiter is in retrograde?

Here are some simple recipes for what Flask-Rebar currently supports:


Allow a user with either scope "A" OR scope "B"

.. code-block:: python

	from flask import g
	from my_app import authenticator, registry
	from my_app.scheme import EditStuffSchema, StuffSchema


	# Allow a user with the "admin" scope OR the "edit:stuff" scope
	@registry.handles(
		rule="/stuff/<uid:thing>/",
		method="POST",e
		request_body_schema=EditStuffSchema(),
		response_body_schema=StuffSchema(),
		authenticators=[authenticator.with_scope("admin"), authenticator.with_scope("edit:stuff")]
	)
	def edit_stuff(thing):
		update_stuff(thing, g.validated_body)
		return thing


Allow a request with either valid Auth0 OR an API-Key

.. code-block:: python

	from flask import g
	from flask_rebar.authenticators import HeaderApiKeyAuthenticator
	from flask_rebar_auth0 import get_authenticated_user
	from my_app import authenticator, registry


	# Allow Auth0 or API Key
	@registry.handles(
	    rule="/rate_limit/",
	    method="GET",
	    response_body_schema=RateLimitSchema(),
	    authenticators=[authenticator, HeaderApiKeyAuthenticator("X-API-KEY")]
	)
	def get_limits():
		requester = g.authenticated_app_name or get_authenticated_user()
		rate_limit = get_limits_for_app_or_user(requester)
		return rate_limit


Allow a request with Auth0 AND an API-Key

.. note::
	This currently requires some workarounds. Better support is planned.

.. code-block:: python

	from flask_rebar.authenticators import HeaderApiKeyAuthenticator
	from flask_rebar_auth0 import get_authenticated_user, Auth0Authenticator
	from my_app import authenticator
	from flask_rebar.swagger_generation.authenticator_to_swagger import (
		AuthenticatorConverter, authenticator_converter_registry
	)


	class CombindedAuthenticator(Auth0Authenticator, HeaderApiKeyAuthenticator):

		def __init__(app, header):
			Auth0Authenticator.__init__(self, app)
			HeaderApiKeyAuthenticator.__init__(self, header)

		def authenticate(self):
			authenticator.authenticate(self)
			HeaderAPIKeyAuthenticator.authenticate(self)


	auth0_converter = authenticator_converter_registry._get_converter_for_type(authenticator)
	header_api_converter = authenticator_converter_registry._get_converter_for_type(HeaderApiKeyAuthenticator("header"))

	class CombinedAuthenticatorConverter(AuthenticatorConverter):

		AUTHENTICATOR_TYPE = CombindedAuthenticator

		def get_security_schemes(self, obj, context):
			definition = dict()
			definition.update(auth0_converter.get_security_schemes(obj, context))
			definition.update(header_api_converter.get_security_schemes(obj, context))
			return definition

		def get_security_requirements(self, obj, context):
			auth_requirement = auth0_converter.get_security_requirements(obj, context)[0]
			header_requirement = header_api_converter.get_security_requirements(obj, context)[0]
			combined_requirement = dict()
			combined_requirement.update(auth_requirement)
			combined_requirement.update(header_requirement)

			return [
				combined_requirement
			]


	authenticator_converter_registry.register_type(CombinedAuthenticatorConverter)


	@registry.handles(
	    rule="/user/me/api_token",
	    method="GET",
	    authenticators=CombinedAuthenticatorConverter(app, "X-API-Key")
	)
	def check_token():
		return 200


Marshmallow Partial Schemas
===========================

Beginning with version 1.12, Flask-Rebar includes support for `Marshmallow "partial" loading <https://marshmallow.readthedocs.io/en/stable/quickstart.html#partial-loading>`_ of schemas.  This is particularly useful if you have a complicated schema with lots of required fields for creating an item (e.g., via a POST endpoint) and want to reuse the schema with some or all fields as optional for an update operation (e.g., via PATCH).

While you can accomplish this by simply adding a ``partial`` keyword argument when instantiating an existing schema, to avoid confusion in the generated OpenAPI model, we strongly recommend creating a derived schema class as illustrated in the following example:

.. code-block:: python

	class CreateTodoSchema(RequestSchema):
		complete = fields.Boolean(required=True)
		description = fields.String(required=True)
		created_by = fields.String(required=True)


	class UpdateTodoSchema(CreateTodoSchema):
		def __init__(self, **kwargs):
			super_kwargs = dict(kwargs)
			partial_arg = super_kwargs.pop('partial', True)
			super(UpdateTodoSchema, self).__init__(partial=partial_arg, **super_kwargs)

The preceeding example makes `all` fields from ``CreateTodoSchema`` optional in the derived ``UpdateTodoSchema`` class by injecting ``partial=True`` as a keyword argument.  Marshmallow also supports specifying only some fields as "partial" so if, for example, you wanted to use this approach but make only the ``description`` and ``created_by`` fields optional, you could use something like:

.. code-block:: python

	class UpdateTodoSchema(CreateTodoSchema):
		def __init__(self, **kwargs):
			super_kwargs = dict(kwargs)
			partial_arg = super_kwargs.pop('partial', ['description', 'created_by'])
			super(UpdateTodoSchema, self).__init__(partial=partial_arg, **super_kwargs)


Structuring Larger Projects
===========================

When structuring larger projects, there may be more than one directory which has modules which will be loaded into the ``Registry``.  They still need to be imported, but if there is nothing else to do with them, they aren't used. Instead Flask-Rebar can import those modules.

Let's take a look at this setup:

.. code-block::

	application/
	├── app.py
	├── config.py
	├── database.py
	├── rebar.py
	├── handlers
	│   └── create.py
	├── models
	│   └── data.py
	└── schemas
		├── create.py
		└── sync.py

Inside of rebar.py we can find this:

.. code-block:: python

	from flask_rebar import Rebar

	rebar = Rebar()
	registry = rebar.create_handler_registry(handlers='application.handlers')
	registry.load_handlers(recursive=False)

The ``handlers`` argument to the :class:`flask_rebar.rebar.HandlerRegistry` will be used to look in the ``application.handlers`` package and load all modules that it finds in there, but not recursively.  This will result in all of the handlers getting imported, so that they can be added to the registry, without a having to add a new import to ``application.app`` each time a new file is added to ``application/handlers/``

And because ``registry.load_handlers()`` is run after ``registry`` is defined, importing the ``registry`` object to in all the files imported by ``load_handlers()`` will not cause circular imports.
