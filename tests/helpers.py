import builtins
from flask import json
from werkzeug.utils import cached_property
import pytest


class JsonResponseMixin(object):
    """
    Mixin with testing helper methods
    """

    @cached_property
    def json(self):
        return json.loads(self.data)


def make_test_response(response_class):
    return type("TestResponse", (response_class, JsonResponseMixin), {})


@pytest.fixture
def docstring_parser_not_installed(monkeypatch):
    import_orig = builtins.__import__

    def mocked_import(name, *args, **kwargs):
        if name == "docstring_parser":
            raise ImportError()
        return import_orig(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mocked_import)
