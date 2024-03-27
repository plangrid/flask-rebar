Why Flask-Rebar?
================

There are number of packages out there that solve a similar problem. Here are just a few:

* `Connexion <https://github.com/zalando/connexion>`_
* `Flask-RESTful <https://github.com/flask-restful/flask-restful>`_
* `flask-apispec <https://github.com/jmcarp/flask-apispec>`_
* `Flasgger <https://github.com/rochacbruno/flasgger>`_

These are all great projects, and one might work better for your use case. Flask-Rebar solves a similar problem with its own twist on the approach:

Marshmallow for validation *and* marshaling
-------------------------------------------

Some approaches use Marshmallow only for marshaling, and provide a secondary schema module for request validation.

Flask-Rebar is Marshmallow first. Marshmallow is a well developed, well supported package, and Flask-Rebar is built on top of it from the get go.


Swagger as a side effect
------------------------

Some approaches generate code *from* a Swagger specification, or generate Swagger from docstrings. Flask-Rebar aims to make Swagger (a.k.a. OpenAPI) a byproduct of writing application code with Marshmallow and Flask.

This is really nice if you prefer the rich validation/transformation functionality of Marshmallow over Swagger's more limited set.

It also alleviates the need to manually keep an API's documentation in sync with the actual application code - the schemas used by the application are the same schemas used to generate Swagger.

It's also not always practical - Flask-Rebar sometimes has to expose some Swagger specific things in its interface. C'est la vie.

And since Marshmallow can be more powerful than Swagger, it also means its possible to have validation logic that can't be represented in Swagger. Flask-Rebar assumes this is inevitable, and assumes that it's OK for an API to raise a 400 error that Swagger wasn't expecting.
