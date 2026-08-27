"""Tests for the Pydantic Flask-Rebar adapter."""

import json
import warnings
from typing import Annotated, Generic, TypeVar
from uuid import UUID

import pytest
from flask import Flask
from flask_rebar import Rebar, SwaggerV3Generator, compat

pytest.importorskip("pydantic")

from pydantic import (  # noqa: E402
    BaseModel,
    Field,
    RootModel,
    ValidationError as PydanticValidationError,
    computed_field,
)

from flask_rebar.utils.pydantic_schema import (  # noqa: E402
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
    errors_by_field = {tuple(e["loc"]): e["type"] for e in response.json["errors"]}
    assert errors_by_field == {
        ("name",): "missing",
        ("pageWidth",): "float_parsing",
    }


def test_unknown_fields_are_rejected(client):
    response = client.post(
        "/v1/things",
        json={"name": "x", "pageWidth": 1.0, "unexpected": True},
    )

    assert response.status_code == 400
    [error] = response.json["errors"]
    assert error["loc"] == ["unexpected"]
    assert error["type"] == "extra_forbidden"


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
    with pytest.warns(UserWarning, match="Swagger 2.0"):
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


def test_swagger_v3_generation_does_not_warn(client):
    registry = client.application.config["registry"]
    registry.swagger_generator = SwaggerV3Generator()

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        swagger = registry.swagger_generator.generate_swagger(registry)

    assert "CreateThing" in swagger["components"]["schemas"]


def test_recursive_pydantic_models_keep_a_self_reference_in_swagger():
    class Node(ApiModel):
        name: str
        children: list["Node"] = []

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/nodes",
        method="GET",
        response_body_schema={200: Node},
    )
    def get_node():
        return {"name": "root", "children": []}, 200

    app = Flask(__name__)
    rebar.init_app(app)

    with pytest.warns(UserWarning, match="Swagger 2.0"):
        swagger = registry.swagger_generator.generate_swagger(registry)
    node_schema = swagger["definitions"]["Node"]

    assert node_schema["properties"]["children"]["items"] == {
        "$ref": "#/definitions/Node"
    }


def test_recursive_generic_pydantic_model_self_reference_resolves():
    T = TypeVar("T")

    class Tree(ApiModel, Generic[T]):
        value: T
        children: list["Tree[T]"] = []

    IntTree = Tree[int]
    # Pydantic's stack-based schema rebuild can happen far from the class definition 
    # (e.g. during Swagger generation) but is unreliable in Python 3.10.
    IntTree.model_rebuild()

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/trees",
        method="GET",
        response_body_schema={200: IntTree},
    )
    def get_tree():
        return {"value": 1, "children": []}, 200

    app = Flask(__name__)
    rebar.init_app(app)

    with pytest.warns(UserWarning, match="Swagger 2.0"):
        swagger = registry.swagger_generator.generate_swagger(registry)
    definitions = swagger["definitions"]
    ref = definitions["Treeint"]["properties"]["children"]["items"]["$ref"]

    assert ref.rsplit("/", 1)[-1] in definitions


def test_recursive_pydantic_model_self_reference_keeps_field_overrides():
    class Node(ApiModel):
        name: str
        children: list[Annotated["Node", Field(description="child node")]] = []

    schema = openapi_schema(Node)

    assert schema["properties"]["children"]["items"]["$ref"] == "Node"
    assert schema["properties"]["children"]["items"]["description"] == "child node"


def test_schema_generation_inlines_references_and_drops_property_titles():
    schema = openapi_schema(CreateThing)

    assert "$defs" not in json.dumps(schema)
    assert schema["properties"]["nested"]["title"] == "Nested"
    assert "title" not in schema["properties"]["name"]


def test_omit_none_only_applies_to_rebar_response_dumps():
    nested = Nested(bubble_urn=None, rotation=90)

    assert nested.model_dump(by_alias=True) == {"bubbleUrn": None, "rotation": 90}
    assert schema_for(Nested).dump(nested) == {"rotation": 90}


def test_schema_for_returns_a_fresh_instance_and_supports_plain_models():
    class PlainModel(BaseModel):
        status: str

    # A fresh instance every call, so per-request mutations on one schema
    # (e.g. compat.exclude_unknown_fields toggling .unknown) can't bleed into
    # another registration that reuses the same model in a different role.
    assert schema_for(CreateThing) is not schema_for(CreateThing)
    assert schema_for(PlainModel).load({"status": "ok"}) == PlainModel(status="ok")


def test_excluding_unknown_fields_on_a_headers_schema_does_not_leak_to_other_roles():
    class Shared(ApiModel):
        name: str = Field(alias="Name")

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(rule="/headers-role", method="GET", headers_schema=Shared)
    def use_as_headers():
        return {}, 200

    @registry.handles(rule="/body-role", method="POST", request_body_schema=Shared)
    def use_as_body():
        return {}, 200

    app = Flask(__name__)
    rebar.init_app(app)
    client = app.test_client()

    headers_response = client.get(
        "/v1/headers-role", headers={"name": "x", "another-header": "ignored"}
    )
    assert headers_response.status_code == 200

    body_response = client.post("/v1/body-role", json={"name": "x", "unexpected": True})
    assert body_response.status_code == 400
    [error] = body_response.json["errors"]
    assert error["loc"] == ["unexpected"]


def test_many_loads_and_dumps_a_list_of_models():
    schema = schema_for(CreateThing, many=True)

    loaded = schema.load([{"name": "x", "pageWidth": 1.0}])
    assert loaded == [CreateThing(name="x", pageWidth=1.0)]

    dumped = schema.dump(loaded)
    assert dumped == [{"name": "x", "pageWidth": 1.0, "nested": {}}]


def test_many_load_errors_are_keyed_by_index():
    schema = schema_for(CreateThing, many=True)

    with pytest.raises(PydanticValidationError) as excinfo:
        schema.load([{"name": "x", "pageWidth": 1.0}, {"pageWidth": "wide"}])

    locs = [error["loc"][0] for error in excinfo.value.errors()]
    assert locs == [1, 1]


def test_many_response_body_schema_returns_a_json_array():
    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/things/many",
        method="GET",
        response_body_schema={200: schema_for(ThingResponse, many=True)},
    )
    def list_thing_responses():
        return [
            {
                "uid": UUID("11111111-1111-1111-1111-111111111111"),
                "name": "x",
                "nested": Nested(),
            }
        ], 200

    app = Flask(__name__)
    rebar.init_app(app)
    response = app.test_client().get("/v1/things/many")

    assert response.status_code == 200
    assert response.json == [
        {
            "uid": "11111111-1111-1111-1111-111111111111",
            "name": "x",
            "nested": {},
            "updatedAt": None,
        }
    ]

    with pytest.warns(UserWarning, match="Swagger 2.0"):
        swagger = registry.swagger_generator.generate_swagger(registry)
    responses = swagger["paths"]["/v1/things/many"]["get"]["responses"]
    assert responses["200"]["schema"] == {
        "type": "array",
        "items": {"$ref": "#/definitions/ThingResponse"},
    }
    assert "ThingResponse" in swagger["definitions"]


def test_root_model_lists_work_as_a_pure_pydantic_alternative_to_many():
    """A ``pydantic.RootModel[list[X]]`` is the pure-pydantic way to say "a
    list of X" - pass it straight to a handler like any other model, with
    no ``schema_for(..., many=True)`` needed. Its own component name must
    still resolve to a real Swagger definition, not just the singular
    item's.
    """

    class Item(ApiModel):
        count: int

    class Items(RootModel[list[Item]]):
        pass

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/items",
        method="GET",
        response_body_schema={200: Items},
    )
    def list_items():
        return [{"count": 1}, {"count": 2}], 200

    app = Flask(__name__)
    rebar.init_app(app)
    response = app.test_client().get("/v1/items")

    assert response.status_code == 200
    assert response.json == [{"count": 1}, {"count": 2}]

    with pytest.warns(UserWarning, match="Swagger 2.0"):
        swagger = registry.swagger_generator.generate_swagger(registry)
    ref = swagger["paths"]["/v1/items"]["get"]["responses"]["200"]["schema"]["$ref"]
    definitions = swagger["definitions"]

    assert "Item" in definitions
    assert ref == "#/definitions/Items"
    assert definitions["Items"] == {
        "title": "Items",
        "type": "array",
        "items": {"$ref": "#/definitions/Item"},
    }


def test_colliding_component_names_fail_swagger_generation():
    def make_item_model() -> type[BaseModel]:
        class Item(ApiModel):
            pass

        return Item

    FirstItem = make_item_model()

    class Item(ApiModel):
        count: int

    rebar = Rebar()
    registry = rebar.create_handler_registry(prefix="/v1")

    @registry.handles(
        rule="/first", method="GET", response_body_schema={200: FirstItem}
    )
    def get_first():
        return {}, 200

    @registry.handles(rule="/second", method="GET", response_body_schema={200: Item})
    def get_second():
        return {}, 200

    with pytest.warns(UserWarning, match="Swagger 2.0"), pytest.raises(
        ValueError, match="Item"
    ):
        registry.swagger_generator.generate_swagger(registry)


def test_api_model_keeps_snake_case_fields_and_rejects_unknown_fields():
    class SnakeCaseThing(ApiModel):
        page_width: float

    assert schema_for(SnakeCaseThing).load({"page_width": 1.5}) == SnakeCaseThing(
        page_width=1.5
    )
    with pytest.raises(PydanticValidationError):
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
    response = client.get(
        "/v1/things", headers={"X-Api-Key": "secret", "another-headers": "ignored"}
    )

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
