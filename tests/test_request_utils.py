import unittest

from flask import Flask
from flask_testing import TestCase
from marshmallow import fields, ValidationError

from plangrid import flask_toolbox
from flask_rebar import validation


class TestResponseFormatting(TestCase):

    def create_app(self):
        app = Flask(__name__)

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
