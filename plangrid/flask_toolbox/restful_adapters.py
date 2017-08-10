"""
Tools for making old apps that use Flask-RESTful work with Flask-Toolbox instead.
"""
from newrelic import agent as newrelic_agent
from werkzeug.wrappers import Response

from plangrid.flask_toolbox import response


class RestfulApiAdapter(object):
    """Replacement for the Api class in Flask-RESTful."""
    def __init__(self, blueprint):
        self.blueprint = blueprint

    def add_resource(self, handler, *rules, **kwargs):
        for rule in rules:
            for method in kwargs['methods']:
                view_func = self._make_view_func(handler, method)
                endpoint = method + ' ' + rule
                self.blueprint.add_url_rule(
                    rule=rule,
                    view_func=view_func,
                    endpoint=endpoint,
                    methods=[method]
                )

    def _make_view_func(self, handler, method):
        if not hasattr(handler, method.lower()) \
                or not callable(getattr(handler, method.lower())):
            err = 'Handler {class_name} claims to accept the {http_method} ' \
                  'HTTP method, but has no {method} method on it. ' \
                  'You should add one or edit the methods list.'
            raise NotImplementedError(
                err.format(
                    class_name=handler.__name__,
                    http_method=method,
                    method=method.lower()
                )
            )

        def view_func(*args, **kwargs):
            # Manually set the New Relic transaction name, otherwise it will
            # be '/plangrid.flask_toolbox.restful_adapters:view_func' for all
            # routes, which is less than helpful
            module_name = handler.__module__
            handler_name = handler.__name__.lower()
            newrelic_agent.set_transaction_name('/{}:{}'.format(module_name, handler_name))

            instance = handler()
            func = getattr(instance, method.lower())
            result = func(*args, **kwargs)

            # Some handlers return a response object directly. If that's the
            # case, just go ahead and return it.
            if isinstance(result, Response):
                return result

            # Others return only an object to be serialized as the response
            # body, leaving out the status code. In this case we assume a 200.
            if not isinstance(result, tuple):
                result = result, 200

            return response(data=result[0], status_code=result[1])
        return view_func
