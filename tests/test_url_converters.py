from __future__ import unicode_literals

import uuid

from flask import Flask
from flask_testing import TestCase

from plangrid import flask_toolbox
from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.url_converters import UrlConverters


class TestCustomConverters(TestCase):
    def create_app(self):
        app = Flask(__name__)
        UrlConverters(app)

        @app.route('/stuff/<uuid_string:uid>')
        def route(uid):
            return flask_toolbox.response(data={'uid': uid}, status_code=200)

        return app

    def test_request_with_valid_uid(self):
        uid = str(uuid.uuid4())
        resp = self.app.test_client().get('/stuff/{}'.format(uid))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'uid': uid})

    def test_request_with_invalid_uid(self):
        resp = self.app.test_client().get('/stuff/asdf')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': messages.invalid_uuid})
