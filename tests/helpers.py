from flask import json_available

if json_available:
    from flask import json
from werkzeug.utils import cached_property


class JsonResponseMixin(object):
    """
    Mixin with testing helper methods
    """

    @cached_property
    def json(self):
        if not json_available:  # pragma: no cover
            raise NotImplementedError
        return json.loads(self.data)


def make_test_response(response_class):
    return type("TestResponse", (response_class, JsonResponseMixin), {})
