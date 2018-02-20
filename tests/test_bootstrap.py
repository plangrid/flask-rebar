import uuid

from marshmallow import fields
from flask import Flask
from flask_testing import TestCase

from flask_rebar import ResponseSchema
from flask_rebar import Framer
from flask_rebar import bootstrap_app_with_framer


class TestBootstrapAppWithFramer(TestCase):
    valid_user_id = '5550f21512921d007563c3b0'

    def create_app(self):
        framer = Framer()

        class IndexResponse(ResponseSchema):
            user_id = fields.String()
            request_id = fields.String()

        @framer.handles(
            path='/',
            method='GET',
            marshal_schemas=IndexResponse()
        )
        def index():
            return {
                'user_id': framer.validated_headers['user_id'],
                'request_id': framer.validated_headers['request_id']
            }

        app = Flask(__name__)

        bootstrap_app_with_framer(
            app=app,
            framer=framer,
            set_default_authenticator=True,
            set_default_headers_schema=True
        )

        self.api_key = 'super-secret'
        framer.default_authenticator.register_key(key=self.api_key)

        return app

    def test_missing_user_id_header(self):
        resp = self.app.test_client().get(
            '/',
            headers={
                'X-PG-Auth': self.api_key,
            }
        )

        self.assertEqual(resp.status_code, 400)

    def test_user_id_header(self):
        resp = self.app.test_client().get(
            '/',
            headers={
                'X-PG-Auth': self.api_key,
                'X-PG-UserId': self.valid_user_id
            }
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['user_id'], self.valid_user_id)

    def test_request_id_header_is_defaulted(self):
        resp = self.app.test_client().get(
            '/',
            headers={
                'X-PG-Auth': self.api_key,
                'X-PG-UserId': self.valid_user_id
            }
        )

        self.assertEqual(resp.status_code, 200)
        # Verify that the request id is defaulted to a UUID
        self.assertIsNotNone(resp.json['request_id'])
        uuid.UUID(resp.json['request_id'])  # Nothing blows up!

    def test_invalid_request_id_header(self):
        resp = self.app.test_client().get(
            '/',
            headers={
                'X-PG-Auth': self.api_key,
                'X-PG-UserId': self.valid_user_id,
                'X-PG-RequestId': '123'
            }
        )

        self.assertEqual(resp.status_code, 400)

    def test_request_id_header(self):
        request_id = str(uuid.uuid4())
        resp = self.app.test_client().get(
            '/',
            headers={
                'X-PG-Auth': self.api_key,
                'X-PG-UserId': self.valid_user_id,
                'X-PG-RequestId': request_id
            }
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['request_id'], request_id)
