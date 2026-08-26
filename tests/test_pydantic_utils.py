"""Tests for the Pydantic Flask-Rebar adapter."""

import json
from uuid import UUID

import marshmallow
import pytest
from flask import Flask
from flask_rebar import Rebar, compat

pytest.importorskip("pydantic")

from pydantic import BaseModel, Field, computed_field  # noqa: E402

from flask_rebar.utils.pydantic import (  # noqa: E402
    ApiModel,
    CamelCaseApiModel,
    DateTime,
    OmitNone,
    openapi_schema,
    schema_for,
    validated_args,
    validated_body,
    validated_headers,
)


class Nested(OmitNone, CamelCaseApiModel):
    bubble_urn: str | None = None
    rotation: int | None = None


class CreateThing(CamelCaseApiModel):
    name: str
    page_width: float
    nested: Nested = Nested()


class ThingResponse(CamelCaseApiModel):
    uid: UUID
    name: str
    updated_at: DateTime | None = None
    nested: Nested


class ThingQuery(CamelCaseApiModel):
    limit: int = 20
    tags: list[str] = Field(default_factory=list)


@pytest.fixture(name="client")
def client_fixture():
    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/things",
        method="POST",
        request_body_schema=CreateThing,
        response_body_schema={200: ThingResponse},
    )
    def create_thing():
        body = validated_body(CreateThing)
        assert isinstance(body, CreateThing)
        return {
            "uid": UUID("11111111-1111-1111-1111-111111111111"),
            "name": body.name,
            "nested": body.nested,
        }, 200

    @registry.handles(
        rule="/things",
        method="GET",
        query_string_schema=ThingQuery,
    )
    def list_things():
        args = validated_args(ThingQuery)
        assert isinstance(args, ThingQuery)
        return {"limit": args.limit, "tags": args.tags}, 200

    app = Flask(__name__)
    rebar.init_app(app)
    app.config["registry"] = registry
    return app.test_client()


def test_request_body_loads_as_a_pydantic_model(client):
    response = client.post("/v1/things", json={"name": "x", "pageWidth": 1.5})

    assert response.status_code == 200
    assert response.json["name"] == "x"


def test_validation_errors_keep_the_rebar_error_shape(client):
    response = client.post("/v1/things", json={"pageWidth": "wide"})

    assert response.status_code == 400
    assert response.json["rebar_error_code"] == "body_validation_failed"
    assert response.json["errors"] == {
        "name": "Field required",
        "pageWidth": "Input should be a valid number, unable to parse string as a number",
    }


def test_unknown_fields_are_rejected(client):
    response = client.post(
        "/v1/things",
        json={"name": "x", "pageWidth": 1.0, "unexpected": True},
    )

    assert response.status_code == 400
    assert "unexpected" in response.json["errors"]


def test_response_omits_none_values(client):
    response = client.post("/v1/things", json={"name": "x", "pageWidth": 1.0})

    assert response.status_code == 200
    assert response.json["nested"] == {}


def test_datetime_keeps_the_offset_format():
    dumped = schema_for(ThingResponse).dump(
        {
            "uid": UUID("11111111-1111-1111-1111-111111111111"),
            "name": "x",
            "updated_at": "2026-01-02T03:04:05+00:00",
            "nested": Nested(),
        }
    )

    assert dumped["updatedAt"] == "2026-01-02T03:04:05+00:00"


def test_query_strings_are_coerced_and_support_repeated_parameters(client):
    response = client.get("/v1/things?limit=5&tags=first&tags=second")

    assert response.status_code == 200
    assert response.json == {"limit": 5, "tags": ["first", "second"]}


def test_query_string_validation_errors(client):
    response = client.get("/v1/things?limit=lots")

    assert response.status_code == 400
    assert response.json["rebar_error_code"] == "query_string_validation_failed"


def test_pydantic_models_generate_swagger_definitions(client):
    registry = client.application.config["registry"]
    swagger = registry.swagger_generator.generate_swagger(registry)
    schemas = swagger["definitions"]

    assert schemas["CreateThing"]["properties"]["nested"] == {
        "$ref": "#/definitions/Nested"
    }
    assert schemas["CreateThing"]["required"] == ["name", "pageWidth"]
    assert schemas["ThingResponse"]["properties"]["nested"] == {
        "$ref": "#/definitions/Nested"
    }
    assert "rotation" in schemas["Nested"]["properties"]


def test_schema_generation_inlines_references_and_drops_property_titles():
    schema = openapi_schema(CreateThing)

    assert "$defs" not in json.dumps(schema)
    assert schema["properties"]["nested"]["title"] == "Nested"
    assert "title" not in schema["properties"]["name"]


def test_omit_none_only_applies_to_rebar_response_dumps():
    nested = Nested(bubble_urn=None, rotation=90)

    assert nested.model_dump(by_alias=True) == {"bubbleUrn": None, "rotation": 90}
    assert schema_for(Nested).dump(nested) == {"rotation": 90}


def test_schema_for_is_cached_and_supports_plain_models():
    class PlainModel(BaseModel):
        status: str

    assert schema_for(CreateThing) is schema_for(CreateThing)
    assert schema_for(PlainModel).load({"status": "ok"}) == PlainModel(status="ok")


def test_api_model_keeps_snake_case_fields_and_rejects_unknown_fields():
    class SnakeCaseThing(ApiModel):
        page_width: float

    assert schema_for(SnakeCaseThing).load({"page_width": 1.5}) == SnakeCaseThing(
        page_width=1.5
    )
    with pytest.raises(marshmallow.ValidationError):
        schema_for(SnakeCaseThing).load({"pageWidth": 1.5})


def test_headers_schema_ignores_incidental_headers():
    class ThingHeaders(ApiModel):
        api_key: str = Field(alias="X-Api-Key")

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/things",
        method="GET",
        headers_schema=ThingHeaders,
    )
    def get_thing():
        headers = validated_headers(ThingHeaders)
        assert isinstance(headers, ThingHeaders)
        return {"api_key": headers.api_key}, 200

    app = Flask(__name__)
    rebar.init_app(app)
    client = app.test_client()

    # A real request always carries headers (Host, User-Agent, ...) beyond the
    # ones declared on the schema; those must not fail validation.
    response = client.get("/v1/things", headers={"X-Api-Key": "secret", 'another-headers': 'ignored'})

    assert response.status_code == 200
    assert response.json == {"api_key": "secret"}


def test_validate_on_dump_does_not_reload_computed_fields():
    """compat.dump's validate_on_dump re-load must be skipped for Pydantic
    schemas: it always validates in dump() already, and re-loading its own
    dump output would reject computed fields under ApiModel's extra="forbid".
    """

    class ComputedThing(ApiModel):
        name: str

        @computed_field  # type: ignore[prop-decorator]
        @property
        def name_upper(self) -> str:
            return self.name.upper()

    rebar = Rebar()
    app = Flask(__name__)
    rebar.init_app(app)

    with app.app_context():
        rebar.validate_on_dump = True
        result = compat.dump(schema_for(ComputedThing), ComputedThing(name="x"))

    assert result == {"name": "x", "name_upper": "X"}


def test_a_plain_dict_response_is_validated_and_coerced_through_the_model():
    """A handler doesn't have to construct the response model itself: a plain
    dict is run through Pydantic's own validation/coercion (e.g. a numeric
    string becomes an int) before being dumped, and keys the model doesn't
    know about are dropped rather than tripping ApiModel's extra="forbid".
    """

    class CountResponse(ApiModel):
        count: int
        ratio: float

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/counts",
        method="GET",
        response_body_schema={200: CountResponse},
    )
    def get_counts():
        return {"count": "5", "ratio": 2, "unknown": "dropped"}, 200

    app = Flask(__name__)
    rebar.init_app(app)
    client = app.test_client()

    response = client.get("/v1/counts")

    assert response.status_code == 200
    assert response.json == {"count": 5, "ratio": 2.0}
