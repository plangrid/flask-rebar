"""
    Test Todo
    ~~~~~~~~~

    Tests for the example todo application.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
import json
import sys

import unittest


class TestTodoApp(unittest.TestCase):
    """
    Just some super basic tests to make sure our example app appears to still
    be working.
    """

    @classmethod
    def setUpClass(cls):
        cls.old_path = sys.path.copy()
        sys.path.insert(0, "examples/todo")

    @classmethod
    def tearDownClass(cls):
        sys.path = cls.old_path

    def setUp(self):
        from todo.app import create_app

        self.app = create_app()

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
        self.assertEqual(resp.json["data"][0], {"id": 1, "complete": True, "description": "Find product market fit", "type": "user"})

        resp = self.app.test_client().get(
            "/todos/user",
            headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["data"][0], {"id": 1, "complete": True, "description": "Find product market fit", "type": "user"})

        resp = self.app.test_client().get(
            "/todos/group",
            headers={"X-MyApp-Key": "my-api-key", "Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json["data"])
