"""
    Test Todo
    ~~~~~~~~~

    Tests for the example todo application.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json

import pytest

from examples.todo.todo import create_app


@pytest.fixture
def example_app():
    return create_app(__name__)


def test_swagger(example_app):
    resp = example_app.test_client().get("/swagger")
    assert resp.status_code == 200


def test_authentication(example_app):
    resp = example_app.test_client().get("/todos")
    assert resp.status_code == 401
    resp = example_app.test_client().get(
        "/todos", headers={"X-MyApp-Key": "my-api-key"}
    )
    assert resp.status_code == 200


def test_validation(example_app):
    resp = example_app.test_client().patch(
        "/todos/1",
        headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
        data=json.dumps({"complete": "not a boolean"}),
    )
    assert resp.status_code == 400


def test_crud(example_app):
    resp = example_app.test_client().post(
        "/todos",
        headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
        data=json.dumps({"complete": False, "description": "Find product market fit"}),
    )
    assert resp.status_code == 201

    resp = example_app.test_client().patch(
        "/todos/1",
        headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
        data=json.dumps({"complete": True}),
    )
    assert resp.status_code == 200

    resp = example_app.test_client().get(
        "/todos",
        headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
