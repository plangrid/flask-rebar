from __future__ import unicode_literals

import json
import unittest
import uuid

from plangrid import flask_toolbox
from flask import Flask
from flask import request
from flask_testing import TestCase
from plangrid.flask_toolbox import validation
from marshmallow import ValidationError
from marshmallow import fields

from plangrid.flask_toolbox import http_errors


class TestErrors(TestCase):
    ERROR_MSG = 'Bamboozled!'

    def create_app(self):
        app = Flask(__name__)

        @app.route('/errors', methods=['GET'])
        def a_terrible_handler():
            raise http_errors.Conflict(msg=TestErrors.ERROR_MSG)

        @app.route('/uncaught_errors', methods=['GET'])
        def an_even_worse_handler():
            raise ArithmeticError()

        @app.route('/verbose_errors', methods=['GET'])
        def a_fancy_handler():
            raise http_errors.Conflict(
                msg=TestErrors.ERROR_MSG,
                error_code=123,
                additional_data={'foo': 'bar'}
            )

        flask_toolbox.Toolbox(app)

        return app

    def test_custom_http_errors_are_handled(self):
        resp = self.app.test_client().get('/errors')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json, {'message': TestErrors.ERROR_MSG})

    def test_custom_http_errors_can_have_additional_data(self):
        resp = self.app.test_client().get('/verbose_errors')
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(
            resp.json,
            {'message': TestErrors.ERROR_MSG,
             'foo': 'bar'}
        )

    def test_default_404_errors_are_formatted_correctly(self):
        msg = (
            'The requested URL was not found on the server.  If you entered '
            'the URL manually please check your spelling and try again.'
        )
        resp = self.app.test_client().get('/nonexistent')
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json, {'message': msg})

    def test_default_405_errors_are_formatted_correctly(self):
        msg = 'The method is not allowed for the requested URL.'
        resp = self.app.test_client().put('/errors')
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json, {'message': msg})

    def test_default_500_errors_are_formatted_correctly(self):
        resp = self.app.test_client().get('/uncaught_errors')
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json, {'message': 'Internal Server Error'})


class TestHealthcheck(TestCase):
    def create_app(self):
        app = Flask(__name__)
        flask_toolbox.Toolbox(app)
        return app

    def test_app_gets_a_healthcheck_for_free(self):
        resp = self.app.test_client().get('/health')
        self.assertEqual(resp.status_code, 200)


class TestAuthentication(TestCase):
    AUTH_TOKEN = 'vnhoyb4358ytru943uhterwhurer'
    USER_ID = 'abc123'

    def create_app(self):
        app = Flask(__name__)
        flask_toolbox.Toolbox(app, auth_token=TestAuthentication.AUTH_TOKEN)

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
        self.assertEqual(resp.json, {'message': 'No auth token provided.'})

    def test_401_if_token_is_wrong(self):
        headers = {
            'X-PG-Auth': 'wrronnggo',
            'X-PG-UserId': TestAuthentication.USER_ID
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {'message': 'Invalid authentication.'})

    def test_401_if_user_id_header_is_missing(self):
        headers = {
            'X-PG-Auth': TestAuthentication.AUTH_TOKEN
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json, {'message': 'No user_id provided.'})

    def test_all_good_if_everything_is_valid(self):
        headers = {
            'X-PG-Auth': TestAuthentication.AUTH_TOKEN,
            'X-PG-UserId': TestAuthentication.USER_ID
        }
        resp = self.app.test_client().get('/secrets', headers=headers)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {})


class TestJsonBodyValidation(TestCase):
    def post_json(self, path, data):
        return self.app.test_client().post(
            path=path,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'}
        )

    def create_app(self):
        app = Flask(__name__)
        flask_toolbox.Toolbox(app)

        class NestedSchema(validation.RequestSchema):
            baz = fields.List(fields.Integer())

        class Schema(validation.RequestSchema):
            foo = fields.Integer(required=True)
            bar = fields.Email()
            nested = fields.Nested(NestedSchema)

        @app.route('/stuffs', methods=['POST'])
        def json_body_handler():
            data = flask_toolbox.get_json_body_params_or_400(schema=Schema)
            return flask_toolbox.response(data)

        return app

    def test_json_encoding_validation(self):
        resp = self.app.test_client().post(
            path='/stuffs',
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': 'Fields must be in JSON body.'})

        resp = self.app.test_client().post(
            path='/stuffs',
            data=json.dumps({'foo': 1}),
            headers={'Content-Type': 'text/csv'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json,
            {'message': "Only payloads with 'content-type' "
                        "'application/json' are supported."}
        )

        resp = self.app.test_client().post(
            path='/stuffs',
            data='not valid json',
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': 'Failed to decode JSON body.'})

    def test_json_body_parameter_validation(self):
        # Only field errors
        resp = self.post_json(
            path='/stuffs',
            data={'foo': 'one', 'bar': 'not-an-email'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {
            'message': 'JSON body parameters are invalid.',
            'errors': {
                'foo': 'Not a valid integer.',
                'bar': 'Not a valid email address.'
            }
        })

        # Only general errors
        resp = self.post_json(
            path='/stuffs',
            data={'foo': 1, 'baz': 'This is an unexpected field!'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {
            'message': 'JSON body parameters are invalid.',
            'errors': {'_general': 'Unexpected field: baz'}
        })

        # Both field errors and general errors
        resp = self.post_json(
            path='/stuffs',
            data={'baz': 'This is an unexpected field!'}
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {
            'message': 'JSON body parameters are invalid.',
            'errors': {
                '_general': 'Unexpected field: baz',
                'foo': 'Missing data for required field.'
            }
        })

        # Happy path
        resp = self.post_json(
            path='/stuffs',
            data={'foo': 1}
        )
        self.assertEqual(resp.status_code, 200)

    def test_representing_complex_errors(self):
        resp = self.post_json(
            path='/stuffs',
            data={
                'bam': 'wow!',
                'nested': {
                    'baz': ['one', 'two'],
                    'unexpected': 'surprise!'
                }
            }
        )
        self.assertEqual(resp.status_code, 400)

        self.assertEqual(resp.json, {
            'message': 'JSON body parameters are invalid.',
            'errors': {
                '_general': 'Unexpected field: bam',
                'foo': 'Missing data for required field.',
                'nested': {
                    '_general': 'Unexpected field: unexpected',
                    'baz': {
                        '0': 'Not a valid integer.',
                        '1': 'Not a valid integer.'
                    }
                }
            }
        })


class TestQueryStringValidation(TestCase):
    def create_app(self):
        app = Flask(__name__)
        flask_toolbox.Toolbox(app)

        class Schema(validation.RequestSchema):
            foo = fields.Integer(required=True)
            bar = fields.Boolean()
            baz = validation.CommaSeparatedList(fields.Integer())

        @app.route('/stuffs', methods=['GET'])
        def query_string_handler():
            params = flask_toolbox.get_query_string_params_or_400(schema=Schema())
            return flask_toolbox.response(data=params)

        return app

    def test_query_string_parameter_validation(self):
        resp = self.app.test_client().get(
            path='/stuffs?foo=one'
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {
            'message': 'Query string parameters are invalid.',
            'errors': {
                'foo': 'Not a valid integer.'
            }
        })

        resp = self.app.test_client().get(
            path='/stuffs?bar=true'
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {
            'message': 'Query string parameters are invalid.',
            'errors': {
                'foo': 'Missing data for required field.'
            }
        })

        resp = self.app.test_client().get(
            path='/stuffs?foo=1&unexpected=true'
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {
            'message': 'Query string parameters are invalid.',
            'errors': {'_general': 'Unexpected field: unexpected'}
        })

        resp = self.app.test_client().get(
            path='/stuffs?foo=1&bar=true&baz=1,2,3'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {
            'foo': 1,
            'bar': True,
            'baz': [1, 2, 3]
        })


class TestResponseFormatting(TestCase):
    BASE_URL = 'https://io.plangrid.com'
    PAGINATION_LIMIT_MAX = 100

    def create_app(self):
        app = Flask(__name__)
        flask_toolbox.Toolbox(
            app,
            base_url=self.BASE_URL,
            pagination_limit_max=self.PAGINATION_LIMIT_MAX
        )

        return app

    def test_single_resource_response(self):
        @self.app.route('/single_resource')
        def handler():
            return flask_toolbox.response(data={'foo': 'bar'})

        resp = self.app.test_client().get('/single_resource')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, {'foo': 'bar'})
        self.assertEqual(resp.content_type, 'application/json')

    def test_single_resource_response_with_status_code(self):
        @self.app.route('/single_resource')
        def handler():
            return flask_toolbox.response(data={'foo': 'bar'}, status_code=201)

        resp = self.app.test_client().get('/single_resource')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json, {'foo': 'bar'})
        self.assertEqual(resp.content_type, 'application/json')

    def test_list_response(self):
        @self.app.route('/list_response')
        def handler():
            return flask_toolbox.list_response(
                data=[{'a': 'b'}, {'c': 'd'}],
                additional_data={
                    'foo': 'bar'
                }
            )

        resp = self.app.test_client().get('/list_response')
        self.assertEqual(resp.json, {
            'data': [{'a': 'b'}, {'c': 'd'}],
            'foo': 'bar'
        })
        self.assertEqual(resp.content_type, 'application/json')

    def test_paginated_response(self):
        data = [{'foo': 'bar'}]*100
        total_count = len(data)*2

        @self.app.route('/paginated_response')
        def handler():
            return flask_toolbox.paginated_response(
                data=data,
                total_count=total_count,
                additional_data={
                    'foo': 'bar'
                }
            )

        # When no skip/limit is specified, but the response is paginated
        # with the application defaults, the next_page_url
        # still has skip and limit.
        resp = self.app.test_client().get('/paginated_response')
        self.assertEqual(resp.json, {
            'data': data,
            'foo': 'bar',
            'total_count': total_count,
            'next_page_url': '{}/paginated_response?limit={}&skip={}'.format(
                self.BASE_URL,
                self.PAGINATION_LIMIT_MAX,
                self.PAGINATION_LIMIT_MAX
            )
        })
        self.assertEqual(resp.content_type, 'application/json')

        # If skip/limit is included, the next_page_url is incremented
        resp = self.app.test_client().get(
            '/paginated_response?foo=bar&skip=50&limit=75'
        )
        self.assertEqual(resp.json, {
            'data': data,
            'foo': 'bar',
            'total_count': total_count,
            'next_page_url': '{}/paginated_response?foo=bar&limit=75&skip=125'.format(
                self.BASE_URL
            )
        })
        self.assertEqual(resp.content_type, 'application/json')

    def test_paginated_response_no_next_page(self):
        data = [{'foo': 'bar'}] * 50
        total_count = len(data)

        @self.app.route('/no_next_page')
        def handler():
            return flask_toolbox.paginated_response(
                data=data,
                total_count=total_count
            )

        resp = self.app.test_client().get('/no_next_page?limit=100&skip=100')
        self.assertEqual(resp.json, {
            'data': data,
            'total_count': total_count,
            'next_page_url': None
        })
        self.assertEqual(resp.content_type, 'application/json')


class TestRequestAttributes(TestCase):
    def create_app(self):
        app = Flask(__name__)
        flask_toolbox.Toolbox(app)

        @app.route('/request_info', methods=['GET'])
        def query_string_handler():
            data = {
                'request_id': request.request_id,
                'user_id': request.user_id,
                'auth_token': request.auth_token
            }
            return flask_toolbox.response(data=data)

        return app

    def test_get_request_info_from_headers(self):
        auth_token = '123'
        user_id = '456'
        request_id = '789'

        resp = self.app.test_client().get(
            '/request_info',
            headers={
                'X-PG-Auth': auth_token,
                'X-PG-UserId': user_id,
                'X-PG-RequestId': request_id
            }
        )
        self.assertEqual(resp.json, {
            'request_id': request_id,
            'user_id': user_id,
            'auth_token': auth_token
        })

    def test_get_request_id_is_defaulted(self):
        resp = self.app.test_client().get('/request_info')
        uuid.UUID(resp.json['request_id'])
        # nothing blew up!


class SchemaForMarshaling(validation.ResponseSchema):
    foo = fields.Integer()


class TestMarshal(unittest.TestCase):
    def test_marshal(self):
        marshaled = flask_toolbox.marshal(
            data={'foo': 1},
            schema=SchemaForMarshaling
        )
        self.assertEqual(marshaled, {'foo': 1})

        # Also works with an instance of the schema
        marshaled = flask_toolbox.marshal(
            data={'foo': 1},
            schema=SchemaForMarshaling()
        )

        self.assertEqual(marshaled, {'foo': 1})

    def test_marshal_errors(self):
        with self.assertRaises(ValidationError):
            flask_toolbox.marshal(
                data={'foo': 'bar'},
                schema=SchemaForMarshaling
            )
