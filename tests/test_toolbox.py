from __future__ import unicode_literals

import uuid

from flask import Flask
from flask import request
from flask_testing import TestCase

from plangrid import flask_toolbox
from plangrid.flask_toolbox import bootstrap_app_with_toolbox
from plangrid.flask_toolbox import messages


class TestAuthentication(TestCase):
    AUTH_TOKEN = 'vnhoyb4358ytru943uhterwhurer'
    USER_ID = 'abc123'

    def create_app(self):
        app = Flask(__name__)
        bootstrap_app_with_toolbox(
            app=app,
            config={
                'TOOLBOX_AUTH_TOKEN': TestAuthentication.AUTH_TOKEN
            }
        )

        @app.route('/secrets')
        @flask_toolbox.authenticated
        def authenticated_handler():
            return flask_toolbox.response({})

        return app

    def test_401_if_token_header_is_missing(self):
        headers = {
            'X-PG-UserId': TestAuthentication.USER_ID
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {'message': messages.missing_auth_token})

    def test_401_if_token_is_wrong(self):
        headers = {
            'X-PG-Auth': 'wrronnggo',
            'X-PG-UserId': TestAuthentication.USER_ID
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {'message': messages.invalid_auth_token})

    def test_401_if_user_id_header_is_missing(self):
        headers = {
            'X-PG-Auth': TestAuthentication.AUTH_TOKEN
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {'message': messages.missing_user_id})

    def test_all_good_if_everything_is_valid(self):
        headers = {
            'X-PG-Auth': TestAuthentication.AUTH_TOKEN,
            'X-PG-UserId': TestAuthentication.USER_ID
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {})


class TestRequestAttributes(TestCase):
    def create_app(self):
        app = Flask(__name__)
        bootstrap_app_with_toolbox(app=app)

        @app.route('/request_info', methods=['GET'])
        def query_string_handler():
            data = {
                'request_id': request.request_id,
                'user_id': request.user_id,
                'auth_token': request.auth_token,
                'scopes': list(request.scopes),
                'application_id': request.application_id
            }
            return flask_toolbox.response(data=data)

        return app

    def test_get_request_info_from_headers(self):
        auth_token = '123'
        user_id = '456'
        request_id = '789'
        scope = 'foo'
        application_id = '101'

        resp = self.app.test_client().get(
            '/request_info',
            headers={
                'X-PG-Auth': auth_token,
                'X-PG-UserId': user_id,
                'X-PG-RequestId': request_id,
                'X-PG-Scopes': scope,
                'X-PG-AppId': application_id
            }
        )
        self.assertEqual(resp.json, {
            'request_id': request_id,
            'user_id': user_id,
            'auth_token': auth_token,
            'scopes': [scope],
            'application_id': application_id
        })

    def test_get_request_id_is_defaulted(self):
        resp = self.app.test_client().get('/request_info')
        uuid.UUID(resp.json['request_id'])
        # nothing blew up!

    def test_scopes_are_properly_parsed(self):
        resp = self.app.test_client().get(
            '/request_info',
            headers={'X-PG-Scopes': 'foo bar  baz '}
        )
        self.assertEqual(len(resp.json['scopes']), 3)
        self.assertIn('foo', resp.json['scopes'])
        self.assertIn('bar', resp.json['scopes'])
        self.assertIn('baz', resp.json['scopes'])

        resp = self.app.test_client().get(
            '/request_info',
            headers={'X-PG-Scopes': ''}
        )
        self.assertEqual(resp.json['scopes'], [])

        resp = self.app.test_client().get(
            '/request_info',
            headers={'X-PG-Scopes': ' '}
        )
        self.assertEqual(resp.json['scopes'], [])

        resp = self.app.test_client().get('/request_info')
        self.assertEqual(resp.json['scopes'], [])
