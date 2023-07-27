from flask import json
from werkzeug.utils import cached_property


class JsonResponseMixin:
    """
    Mixin with testing helper methods
    """

    @cached_property
    def json(self):
        return json.loads(self.data)


def make_test_response(response_class):
    return type("TestResponse", (response_class, JsonResponseMixin), {})
