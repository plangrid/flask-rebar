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
           marshal_schema=TodoSchema(),
           method=method,
           request_body_schema=request_body_schema,
       )


This isn't a super slick, classed based interface for Flask-Rebar, but it *is* a way to use unadulterated Flask views to their full intent with minimal `DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_ violations.
