from flask import jsonify

# Tools for making old apps that use Flask-RESTful work with Flask-Toolbox instead.

class RestfulApiAdapter(object):
    """Replacement for the Api class in Flask-RESTful."""
    def __init__(self, blueprint):
        self.blueprint = blueprint

    def add_resource(self, handler, rule, methods):
        for method in methods:
            view_func = self._make_view_func(handler, method)
            endpoint = method + ' ' + rule
            self.blueprint.add_url_rule(rule=rule, view_func=view_func, endpoint=endpoint, methods=[method])

    def _make_view_func(self, handler, method):
        def view_func(*args, **kwargs):
            instance = handler()
            func = getattr(instance, method.lower())
            result, code = func(*args, **kwargs)

            if isinstance(result, dict):
                result = jsonify(result)
            elif result is None:
                result = ''

            return result, code
        return view_func