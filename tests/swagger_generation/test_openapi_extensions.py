"""
Tests for OpenAPI vendor-extension hooks on SwaggerV3Generator.

Two hooks:
  * ``func.__openapi_extensions__`` is deep-merged into the operation
    object for that view function.
  * ``registry.swagger_extensions`` is deep-merged into the final spec
    dict before serialization.
"""

import pytest

import marshmallow as m

from flask_rebar import Rebar
from flask_rebar import openapi_extension, openapi_extensions
from flask_rebar.authenticators import Authenticator
from flask_rebar.swagger_generation import SwaggerV2Generator, SwaggerV3Generator
from flask_rebar.swagger_generation.authenticator_to_swagger import (
    AuthenticatorConverter,
    authenticator_converter_registry,
)
from flask_rebar.swagger_generation.generator_utils import deep_merge


class _FooSchema(m.Schema):
    name = m.fields.String()


def _make_registry():
    rebar = Rebar()
    return rebar.create_handler_registry()


def test_openapi_extension_decorator_single_key():
    registry = _make_registry()

    @registry.handles(
        rule="/foos",
        method="GET",
        response_body_schema={200: _FooSchema()},
    )
    @openapi_extension("x-rate-limit", {"per-minute": 100})
    def list_foos():
        pass

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    op = spec["paths"]["/foos"]["get"]

    assert op["x-rate-limit"] == {"per-minute": 100}
    assert "operationId" in op
    assert "responses" in op


def test_openapi_extensions_decorator_multiple_keys():
    registry = _make_registry()

    @registry.handles(rule="/foos", method="GET")
    @openapi_extensions(**{"x-rate-limit": {"per-minute": 100}, "x-internal": True})
    def list_foos():
        pass

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    op = spec["paths"]["/foos"]["get"]
    assert op["x-rate-limit"] == {"per-minute": 100}
    assert op["x-internal"] is True


def test_openapi_extension_decorators_compose():
    """Stacking decorators on one handler merges their extensions."""
    registry = _make_registry()

    @registry.handles(rule="/foos", method="GET")
    @openapi_extension("x-internal", True)
    @openapi_extension("x-rate-limit", {"per-minute": 100})
    def list_foos():
        pass

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    op = spec["paths"]["/foos"]["get"]
    assert op["x-internal"] is True
    assert op["x-rate-limit"] == {"per-minute": 100}


def test_openapi_extension_rejects_non_x_keys():
    with pytest.raises(ValueError, match="x-"):
        openapi_extension("description", "no")


def test_openapi_extensions_rejects_non_x_keys():
    with pytest.raises(ValueError, match="x-"):
        openapi_extensions(description="no")


def test_no_extensions_attr_is_noop():
    registry = _make_registry()

    @registry.handles(rule="/bar", method="GET")
    def get_bar():
        pass

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    op = spec["paths"]["/bar"]["get"]
    assert not any(k.startswith("x-") for k in op)


def test_extensions_cannot_clobber_standard_keys_silently():
    """Bypassing the decorator's x- check lets you overwrite standard keys.

    The decorator enforces ``x-`` prefix; users that set the attribute
    directly are on their own. Documented here so it's clear what the
    generator does in that case (deep-merge replaces).
    """
    registry = _make_registry()

    @registry.handles(rule="/qux", method="GET")
    def get_qux():
        pass

    get_qux.__openapi_extensions__ = {"summary": "user-supplied summary"}

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    assert spec["paths"]["/qux"]["get"]["summary"] == "user-supplied summary"


def test_registry_swagger_extensions_merged_into_root():
    registry = _make_registry()

    @registry.handles(rule="/foos", method="GET")
    def list_foos():
        pass

    registry.swagger_extensions = {
        "x-vendor-metadata": {"team": "platform"},
        "x-build-id": "abc123",
        "components": {
            "x-spec-link": "https://example.com/spec.yaml",
        },
    }

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    assert spec["x-vendor-metadata"] == {"team": "platform"}
    assert spec["x-build-id"] == "abc123"
    assert spec["components"]["x-spec-link"] == "https://example.com/spec.yaml"


def test_security_scheme_with_vendor_extension_via_converter():
    """Vendor extensions inside a securityScheme go through the existing
    AuthenticatorConverter pattern, not registry.swagger_extensions.

    The converter is free to return ``x-*`` keys alongside the standard
    scheme fields; the generator emits them verbatim.
    """

    class _OAuthAuth(Authenticator):
        def __init__(self, name="vendorOauth"):
            self.name = name

        def authenticate(self):
            pass

    class _OAuthConverter(AuthenticatorConverter):
        AUTHENTICATOR_TYPE = _OAuthAuth

        def get_security_requirements(self, obj, context=None):
            return [{obj.name: []}]

        def get_security_schemes(self, obj, context=None):
            return {
                obj.name: {
                    "type": "oauth2",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "https://example.com/token",
                            "scopes": {},
                            "x-scope-consumers": {
                                "data:read": ["consumer-a"],
                            },
                        }
                    },
                }
            }

    authenticator_converter_registry.register_type(_OAuthConverter())
    rebar = Rebar()
    registry = rebar.create_handler_registry()
    auth = _OAuthAuth()

    @registry.handles(rule="/foos", method="GET", authenticators=auth)
    def list_foos():
        pass

    spec = SwaggerV3Generator().generate(registry, sort_keys=False)
    scheme = spec["components"]["securitySchemes"]["vendorOauth"]
    assert scheme["flows"]["clientCredentials"]["x-scope-consumers"] == {
        "data:read": ["consumer-a"]
    }
    # Op picks up the requirement.
    assert {"vendorOauth": []} in spec["paths"]["/foos"]["get"]["security"]


def test_v2_func_openapi_extensions_merged_into_operation():
    registry = _make_registry()

    @registry.handles(rule="/foos", method="GET")
    @openapi_extension("x-rate-limit", {"per-minute": 100})
    def list_foos():
        pass

    spec = SwaggerV2Generator().generate(registry=registry, sort_keys=False)
    op = spec["paths"]["/foos"]["get"]
    assert op["x-rate-limit"] == {"per-minute": 100}
    assert "operationId" in op


def test_v2_registry_swagger_extensions_merged_into_root():
    registry = _make_registry()

    @registry.handles(rule="/foos", method="GET")
    def list_foos():
        pass

    registry.swagger_extensions = {
        "x-vendor-metadata": {"team": "platform"},
        "x-build-id": "abc123",
    }

    spec = SwaggerV2Generator().generate(registry=registry, sort_keys=False)
    assert spec["x-vendor-metadata"] == {"team": "platform"}
    assert spec["x-build-id"] == "abc123"


def test_v2_no_extensions_attr_is_noop():
    registry = _make_registry()

    @registry.handles(rule="/bar", method="GET")
    def get_bar():
        pass

    spec = SwaggerV2Generator().generate(registry=registry, sort_keys=False)
    op = spec["paths"]["/bar"]["get"]
    assert not any(k.startswith("x-") for k in op)


def test_deep_merge_helper():
    base = {"a": 1, "nested": {"x": 1, "y": 2}}
    overlay = {"b": 2, "nested": {"y": 99, "z": 3}}
    deep_merge(base, overlay)
    assert base == {"a": 1, "b": 2, "nested": {"x": 1, "y": 99, "z": 3}}
    # Overlay untouched.
    assert overlay == {"b": 2, "nested": {"y": 99, "z": 3}}
