"""
    Test Todo
    ~~~~~~~~~

    Tests for the example todo application.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json
import unittest

from examples.todo.todo import create_app


class TestTodoApp(unittest.TestCase):
    """
    Just some super basic tests to make sure our example app appears to still
    be working.
    """

    def setUp(self):
        self.app = self.create_app()

    def create_app(self):
        return create_app(__name__)

    def test_swagger(self):
        resp = self.app.test_client().get("/swagger")
        self.assertEqual(resp.status_code, 200)

    def test_authentication(self):
        resp = self.app.test_client().get("/todos")
        self.assertEqual(resp.status_code, 401)
        resp = self.app.test_client().get(
            "/todos",
            headers={"X-MyApp-Key": "my-api-key"},
            data=json.dumps({"complete": False}),
        )
        self.assertEqual(resp.status_code, 200)

    def test_validation(self):
        resp = self.app.test_client().patch(
            "/todos/1",
            headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
            data=json.dumps({"complete": "not a boolean"}),
        )
        self.assertEqual(resp.status_code, 400)

    def test_crud(self):
        resp = self.app.test_client().post(
            "/todos",
            headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
            data=json.dumps(
                {"complete": False, "description": "Find product market fit"}
            ),
        )
        self.assertEqual(resp.status_code, 201)

        resp = self.app.test_client().patch(
            "/todos/1",
            headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
            data=json.dumps({"complete": True}),
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.app.test_client().get(
            "/todos",
            headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
