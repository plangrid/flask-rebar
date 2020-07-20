import unittest
from flask_rebar.compat import MARSHMALLOW_V3
from flask import json_available

if json_available:
    from flask import json
from werkzeug.utils import cached_property

skip_if_marshmallow_not_v3 = unittest.skipIf(
    not MARSHMALLOW_V3, reason="Only applicable for Marshmallow version 3"
)


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
