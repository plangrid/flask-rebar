import json
import unittest

import marshmallow as m
from flask import Flask

from flask_rebar import HeaderApiKeyAuthenticator
from flask_rebar.authenticators import USE_DEFAULT
from flask_rebar.rebar import Rebar
from flask_rebar.testing import validate_swagger


DEFAULT_AUTH_HEADER = 'x-default-auth'
DEFAULT_AUTH_SECRET = 'SECRET!'
DEFAULT_RESPONSE = {'uid': '0', 'name': "I'm the default for testing!"}


class FooSchema(m.Schema):
    uid = m.fields.String()
    name = m.fields.String()


class ListOfFooSchema(m.Schema):
    data = m.fields.Nested(FooSchema, many=True)


class FooUpdateSchema(m.Schema):
    name = m.fields.String()


class FooListSchema(m.Schema):
    name = m.fields.String(required=True)


class HeadersSchema(m.Schema):
    name = m.fields.String(load_from='x-name', required=True)


class MeSchema(m.Schema):
    user_name = m.fields.String()


def get_json_from_resp(resp):
    return json.loads(resp.data.decode('utf-8'))


def get_swagger(test_client):
    return get_json_from_resp(test_client.get('/swagger'))


def auth_headers(header=DEFAULT_AUTH_HEADER, secret=DEFAULT_AUTH_SECRET):
    return dict([(header, secret)])


def create_framed_app(rebar):
    app = Flask('FramerTest')
    app.testing = True
    rebar.init_app(app)

    default_authenticator = HeaderApiKeyAuthenticator(
        header=DEFAULT_AUTH_HEADER,
        name='default'
    )
    default_authenticator.register_key(
        app_name='internal',
        key=DEFAULT_AUTH_SECRET
    )
    rebar.set_default_authenticator(default_authenticator)

    return app


def register_default_authenticator(rebar):
    default_authenticator = HeaderApiKeyAuthenticator(
        header=DEFAULT_AUTH_HEADER,
        name='default'
    )
    default_authenticator.register_key(
        app_name='internal',
        key=DEFAULT_AUTH_SECRET
    )
    rebar.set_default_authenticator(default_authenticator)


def register_endpoint(
        rebar,
        func=None,
        path='/foos/<foo_uid>',
        method='GET',
        endpoint=None,
        marshal_schemas=None,
        query_string_schema=None,
        request_body_schema=None,
        headers_schema=None,
        authenticator=USE_DEFAULT
):
    def default_handler_func(*args, **kwargs):
        return DEFAULT_RESPONSE

    rebar.add_handler(
        func=func or default_handler_func,
        path=path,
        method=method,
        endpoint=endpoint,
        marshal_schemas=marshal_schemas or {200: FooSchema()},
        query_string_schema=query_string_schema,
        request_body_schema=request_body_schema,
        headers_schema=headers_schema,
        authenticator=authenticator
    )


class FramerTest(unittest.TestCase):
    def test_default_authentication(self):
        rebar = Rebar()
        register_default_authenticator(rebar)
        register_endpoint(rebar)
        app = create_framed_app(rebar)

        resp = app.test_client().get(
            path='/foos/1',
            headers=auth_headers()
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().get(
            path='/foos/1',
            headers=auth_headers(secret='LIES!')
        )
        self.assertEqual(resp.status_code, 401)

    def test_override_authenticator(self):
        auth_header = 'x-overridden-auth'
        auth_secret = 'BLAM!'

        rebar = Rebar()

        register_default_authenticator(rebar)
        authenticator = HeaderApiKeyAuthenticator(header=auth_header)
        authenticator.register_key(app_name='internal', key=auth_secret)

        register_endpoint(rebar, authenticator=authenticator)
        app = create_framed_app(rebar)

        resp = app.test_client().get(
            path='/foos/1',
            headers=auth_headers(header=auth_header, secret=auth_secret)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        # The default authentication doesn't work anymore!
        resp = app.test_client().get(
            path='/foos/1',
            headers=auth_headers()
        )
        self.assertEqual(resp.status_code, 401)

    def test_override_with_no_authenticator(self):
        rebar = Rebar()
        register_default_authenticator(rebar)
        register_endpoint(rebar, authenticator=None)
        app = create_framed_app(rebar)

        resp = app.test_client().get(path='/foos/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

    def test_validate_body_parameters(self):
        rebar = Rebar()

        @rebar.handles(
            path='/foos/<foo_uid>',
            method='PATCH',
            marshal_schemas={
                200: FooSchema()
            },
            request_body_schema=FooUpdateSchema(),
        )
        def update_foo(foo_uid):
            return {'uid': foo_uid, 'name': rebar.validated_body['name']}

        app = create_framed_app(rebar)

        resp = app.test_client().patch(
            path='/foos/1',
            data=json.dumps({'name': 'jill'}),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            get_json_from_resp(resp),
            {'uid': '1', 'name': 'jill'}
        )

        resp = app.test_client().patch(
            path='/foos/1',
            data=json.dumps({'name': 123}),  # Name should be string, not int
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(resp.status_code, 400)

    def test_validate_query_parameters(self):
        rebar = Rebar()

        @rebar.handles(
            path='/foos',
            method='GET',
            marshal_schemas={
                200: ListOfFooSchema()
            },
            query_string_schema=FooListSchema(),
        )
        def list_foos():
            return {
                'data': [{'name': rebar.validated_args['name'], 'uid': '1'}]
            }

        app = create_framed_app(rebar)

        resp = app.test_client().get(path='/foos?name=jill')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            get_json_from_resp(resp),
            {'data': [{'uid': '1', 'name': 'jill'}]}
        )

        resp = app.test_client().get(
            path='/foos?foo=bar'  # missing required parameter
        )
        self.assertEqual(resp.status_code, 400)

    def test_validate_headers(self):
        rebar = Rebar()
        register_default_authenticator(rebar)

        @rebar.handles(
            path='/me',
            method='GET',
            marshal_schemas={
                200: MeSchema(),
            },
            headers_schema=HeadersSchema()
        )
        def get_me():
            return {
                'user_name': rebar.validated_headers['name']
            }

        app = create_framed_app(rebar)

        headers = auth_headers()
        headers['x-name'] = 'hello'

        resp = app.test_client().get(
            path='/me',
            headers=headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            get_json_from_resp(resp),
            {'user_name': 'hello'}
        )

        resp = app.test_client().get(
            path='/me',
            headers=auth_headers()  # Missing the x-name header!
        )
        self.assertEqual(resp.status_code, 400)

    def test_swagger_endpoint_is_automatically_created(self):
        rebar = Rebar()
        app = create_framed_app(rebar)

        resp = app.test_client().get('/swagger')

        self.assertEqual(resp.status_code, 200)

        validate_swagger(get_json_from_resp(resp))

    def test_swagger_ui_endpoint_is_automatically_created(self):
        rebar = Rebar()
        app = create_framed_app(rebar)

        resp = app.test_client().get('/swagger/ui/')

        self.assertEqual(resp.status_code, 200)

    def test_register_multiple_paths(self):
        rebar = Rebar()

        common_kwargs = {
            'method': 'GET',
            'marshal_schemas': {200: FooSchema()},
        }

        @rebar.handles(path='/bars/<foo_uid>', endpoint='bar', **common_kwargs)
        @rebar.handles(path='/foos/<foo_uid>', endpoint='foo', **common_kwargs)
        def handler_func(foo_uid):
            return DEFAULT_RESPONSE
        app = create_framed_app(rebar)

        resp = app.test_client().get(path='/foos/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().get(path='/bars/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        swagger = get_swagger(test_client=app.test_client())
        self.assertIn('/bars/{foo_uid}', swagger['paths'])
        self.assertIn('/foos/{foo_uid}', swagger['paths'])

    def test_register_multiple_methods(self):
        rebar = Rebar()

        common_kwargs = {
            'path': '/foos/<foo_uid>',
            'marshal_schemas': {200: FooSchema()},
        }

        @rebar.handles(method='GET', endpoint='get_foo', **common_kwargs)
        @rebar.handles(method='PATCH', endpoint='update_foo', **common_kwargs)
        def handler_func(foo_uid):
            return DEFAULT_RESPONSE
        app = create_framed_app(rebar)

        resp = app.test_client().get(path='/foos/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().patch(path='/foos/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(get_json_from_resp(resp), DEFAULT_RESPONSE)

        resp = app.test_client().post(path='/foos/1')
        self.assertEqual(resp.status_code, 405)

        swagger = get_swagger(test_client=app.test_client())
        self.assertIn('get', swagger['paths']['/foos/{foo_uid}'])
        self.assertIn('patch', swagger['paths']['/foos/{foo_uid}'])

    def test_default_headers(self):
        rebar = Rebar()
        rebar.set_default_headers_schema(HeadersSchema())

        @rebar.handles(
            path='/me',
            method='GET',
            marshal_schemas=MeSchema()
        )
        def get_me():
            return {
                'user_name': rebar.validated_headers['name']
            }

        @rebar.handles(
            path='/myself',
            method='GET',
            marshal_schemas=MeSchema(),

            # Let's make sure this can be overridden
            headers_schema=None
        )
        def get_myself():
            return DEFAULT_RESPONSE

        app = create_framed_app(rebar)

        resp = app.test_client().get(
            path='/me',
            headers={'x-name': 'hello'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            get_json_from_resp(resp),
            {'user_name': 'hello'}
        )

        resp = app.test_client().get(
            path='/me',
        )
        self.assertEqual(resp.status_code, 400)

        resp = app.test_client().get(
            path='/myself',
        )
        self.assertEqual(resp.status_code, 200)

        swagger = get_swagger(test_client=app.test_client())
        self.assertEqual(
            swagger['paths']['/me']['get']['parameters'][0]['name'],
            'x-name'
        )
        self.assertNotIn(
            'parameters',
            swagger['paths']['/myself']['get']
        )

    def test_swagger_endpoints_can_be_omitted(self):
        rebar = Rebar(config={'REBAR_SWAGGER_PATH': None, 'REBAR_SWAGGER_UI_PATH': ''})
        app = create_framed_app(rebar)

        resp = app.test_client().get('/swagger')
        self.assertEqual(resp.status_code, 404)

        resp = app.test_client().get('/swagger/ui')
        self.assertEqual(resp.status_code, 404)
