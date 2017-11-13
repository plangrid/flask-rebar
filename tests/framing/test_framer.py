import json

import marshmallow as m
from flask import Flask
from flask import request
from flask_testing import TestCase

from plangrid.flask_toolbox import Toolbox, HeaderApiKeyAuthenticator
from plangrid.flask_toolbox.framing.framer import Framer
from plangrid.flask_toolbox.validation import ListOf
from plangrid.flask_toolbox.testing import validate_swagger


# Still some things to test:
# TODO: This works with blueprints
# TODO: Failure scenarios!

class FlaskToSwaggerTest(TestCase):
    def create_app(self):
        app = Flask('FlaskToSwaggerTest')
        framer = Framer()

        class FooSchema(m.Schema):
            uid = m.fields.String()
            name = m.fields.String()

        class FooUpdateSchema(m.Schema):
            name = m.fields.String()

        class FooListSchema(m.Schema):
            name = m.fields.String()

        class HeadersSchema(m.Schema):
            name = m.fields.String(load_from='x-name')

        class MeSchema(m.Schema):
            app_name = m.fields.String()
            user_name = m.fields.String()

        authenticator = HeaderApiKeyAuthenticator(header='x-auth')
        default_authenticator = HeaderApiKeyAuthenticator(
            header='x-another',
            name='default'
        )
        authenticator.register_key(app_name='internal', key='SECRET!')
        default_authenticator.register_key(app_name='internal', key='SECRET!')

        @framer.handles(
            path='/foos/<foo_uid>',
            method='GET',
            marshal_schemas={
                200: FooSchema()
            }
        )
        def get_foo(foo_uid):
            return {'uid': foo_uid, 'name': 'sam'}

        @framer.handles(
            path='/foos/<foo_uid>',
            method='PATCH',
            marshal_schemas={
                200: FooSchema()
            },
            request_body_schema=FooUpdateSchema(),
            authenticator=None
        )
        def update_foo(foo_uid):
            return {'uid': foo_uid, 'name': request.validated_body['name']}

        @framer.handles(
            path='/foos',
            method='GET',
            marshal_schemas={
                200: ListOf(FooSchema)()
            },
            query_string_schema=FooListSchema(),
            authenticator=None
        )
        def list_foos():
            return {
                'data': [{'name': request.validated_args['name'], 'uid': '1'}]
            }

        @framer.handles(
            path='/me',
            method='GET',
            marshal_schemas={
                200: MeSchema(),
            },
            headers_schema=HeadersSchema(),
            authenticator=authenticator
        )
        def get_me():
            return {
                'app_name': request.authenticated_app_name,
                'user_name': request.validated_headers['name']
            }

        framer.set_default_authenticator(default_authenticator)

        Toolbox(app)
        framer.register(app)

        return app

    def test_get_foo(self):
        resp = self.app.test_client().get(
            path='/foos/1',
            headers={'x-another': 'SECRET!'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'uid': '1', 'name': 'sam'})

    def test_update_foo(self):
        resp = self.app.test_client().patch(
            path='/foos/1',
            data=json.dumps({'name': 'jill'}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'uid': '1', 'name': 'jill'})

    def test_list_foos(self):
        resp = self.app.test_client().get(
            path='/foos?name=jill'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'data': [{'uid': '1', 'name': 'jill'}]})

    def test_get_me(self):
        resp = self.app.test_client().get(
            path='/me',
            headers={'x-name': 'hello', 'x-auth': 'SECRET!'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'app_name': 'internal', 'user_name': 'hello'})

    def test_swagger(self):
        resp = self.app.test_client().get('/swagger')

        self.assertEqual(resp.status_code, 200)

        validate_swagger(resp.json)

    def test_swagger_ui(self):
        resp = self.app.test_client().get('/swagger/ui/')

        self.assertEqual(resp.status_code, 200)
