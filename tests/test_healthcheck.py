from __future__ import unicode_literals

from flask import Flask
from flask_testing import TestCase

from plangrid.flask_toolbox.healthcheck import Healthcheck


class TestHealthcheck(TestCase):
    def create_app(self):
        app = Flask(__name__)
        Healthcheck(app)
        return app

    def test_app_gets_a_healthcheck_for_free(self):
        resp = self.app.test_client().get('/health')
        self.assertEqual(resp.status_code, 200)
