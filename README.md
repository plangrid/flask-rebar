Flask Toolbox
=============

Utilities for building a RESTful PlanGrid service.


Summary
-------

What you get:

- **Request and Response Validation** - Flask-toolbox is designed to work with [marshmallow](https://marshmallow.readthedocs.io/en/latest/) and is packaged with some common additions (e.g. validating against unexpected fields in request bodies).
- **Authentication** - More specifically... lightweight backend service authentication.
- **Error Handling** - All you need to do to get a proper JSON HTTP error response is throw an exception.
- **Bugsnag Configuration** - Flask-toolbox forwards uncaught exceptions to Bugsnag.
- **Healthcheck** - Kubernetes expects a healthcheck to know if a service was properly deployed - flask-toolbox includes one out of the box.
- **Automatic Swagger Generation** - No need to manually maintain a massive .yaml file.

What you don't get:

- **Auto-generated CRUD** - Flask-toolbox tries to be fairly un-opinionated, and doesn't make any assumptions about a service's database or business logic.
- **Guaranteed Adherence to PlanGrid API Standards** - It's still up to you to make sure we're staying consistent with how PlanGrid does REST. As those standards become more and more finalized, flask-toolbox can start enforcing them.
- **Content Negotiation** - Just application/json for now


Installation
------------

This package is deployed to our local Python package index.

```
pip install plangrid.flask-toolbox
```


Package Makeup
--------------

The bulk of Flask-toolbox is a smorgasbord of Flask extensions:

- **bugsnag** - reports errors to Bugsnag
- **errors** - translates Python exceptions to HTTP errors
- **framing** - declarative REST handlers with automatic swagger generation
- **healthcheck** - PlanGrid compliant healthcheck for Kubernetes
- **pagination** - utilities for paginated requests
- **url_converters** - additional converters for Flask URL parameters
- **toolbox (DEPRECATED)** - there used to be a single extension in the toolbox that included several of the above. This functionality was broken out into modular extensions, and now this extensions only includes some authentication stuff. This has been deprecated in favor of `framing`.

While these extensions are nice and composable, there are recommended ways to bundle them up. Functions to create these bundles live in the [plangrid/flask_toolbox/bootstrap.py](plangrid/flask_toolbox/bootstrap.py) file. These functions serve as main entry points into this package and should be called at application startup.


Example Usage
-------------

Check out the example app at [examples/todo.py](examples/todo.py). Some example requests to this example app can be found at [examples/todo_output.md](examples/todo_output.md).


Configuration
-------------

Flask-toolbox looks for the following environment variables:

| Environment Variable | Description | Default |
| -------------------- | ----------- | ------- |
| TOOLBOX_PAGINATION_LIMIT_MAX | The default page size limit for pagination requests. | `100` |
| BUGSNAG_API_KEY | The API key to use for notifying Bugsnag of errors. | `None` |
| BUGSNAG_RELEASE_STAGE | The release stage to use in Bugsnag notifications. | `'production'` |
| TOOLBOX_FRAMER_ADD_SWAGGER_ENDPOINTS | Adds auto-generated swagger endpoints to the service | `True` |
| TOOLBOX_FRAMER_SWAGGER_PATH | The path to retrieve the swagger JSON spec for the service | `'/swagger'` |
| TOOLBOX_FRAMER_SWAGGER_UI_PATH | The path to view HTML docs for the service generated from swagger | `'/swagger/ui'` |


Authentication
--------------

Flask-toolbox is designed for *internal* PlanGrid services, i.e. services inside our VPC, with requests from external clients proxied by an edge router.
Consequently, the only authentication mechanism included in this box is simple API key authentication, where all requests are assumed to be *internal and trusted*.

Clients may include an `X-PG-Auth` header, where the value is a shared secret. Clients may also include a `X-PG-UserId` header, where the value is a user object's unique identifier.

A Flask-toolbox application can be configured to be aware of multiple different API keys, making zero-downtime key rotation possible.
It can also be configured to associate different keys with different application, which can be useful for rudimentary application authorization.


Swagger Generation
------------------

Flask-toolbox can automatically generate a Swagger specification from the declarative routing of the `Framer`.
The same marshmallow schemas used to validate incoming requests and marshal outgoing data are used to generate the Swagger.

Converters for most of Marshmallow's fields and validators are included here.
The converters also inspect a Marshmallow schema/field/validator's method resolution order, so subclassing Marshmallow objects should work without much trouble.
With that, the Marshmallow to Swagger converter is extendable, allowing for custom handling of custom Marshmallow types.
