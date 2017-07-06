import json
from unittest import TestCase

from flask import Blueprint
from flask import Flask

from plangrid.flask_toolbox import Toolbox
from plangrid.flask_toolbox.restful_adapters import RestfulApiAdapter
from plangrid.flask_toolbox.http_errors import BadRequest

class TestRestfulApiAdapter(TestCase):
    def make_app(self, handler, route, methods):
        app = Flask(__name__)
        Toolbox(app)
        blueprint = Blueprint('test', __name__)
        adapter = RestfulApiAdapter(blueprint)
        adapter.add_resource(handler, route, methods)
        app.register_blueprint(blueprint)
        return app

    def test_http_methods(self):
        client = self.make_app(SimpleHandler, '/thing', ['GET', 'POST']).test_client()

        resp = client.get('/thing')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, 'hello')

        resp = client.post('/thing')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data, 'goodbye')

        resp = client.delete('/thing')
        self.assertEqual(resp.status_code, 405)

        resp = client.get('/stuff')
        self.assertEqual(resp.status_code, 404)

    def test_dict_response(self):
        client = self.make_app(DictRespondingHandler, '/dict', ['GET']).test_client()
        resp = client.get('/dict')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data), TEST_DICT)

    def test_empty_response(self):
        client = self.make_app(EmptyResponseHandler, '/nothing', ['GET']).test_client()
        resp = client.get('/nothing')
        self.assertEqual(resp.data, '')

    def test_kwargs(self):
        client = self.make_app(KwargsHandler, '/exclaim/<string:word>', ['GET']).test_client()
        resp = client.get('/exclaim/hello')
        self.assertEqual(resp.data, 'hello!')

    def test_error_handler(self):
        app = self.make_app(ErrorThrowingHandler, '/error', ['GET'])
        client = app.test_client()
        resp = client.get('/error')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json.loads(resp.data)['message'], BadRequest.default_message)

TEST_DICT = {'some': 'stuff', 'in_a': 'dict'}

class SimpleHandler:
    def get(self):
        return 'hello', 200
    def post(self):
        return 'goodbye', 201

class DictRespondingHandler:
    def get(self):
        return TEST_DICT, 200

class EmptyResponseHandler:
    def get(self):
        return None, 204

class KwargsHandler:
    def get(self, word):
        return '{}!'.format(word), 200

class ErrorThrowingHandler:
    def get(self):
        raise BadRequest()