from flask_testing import TestCase
from flask import Blueprint
from flask import Flask

from plangrid.flask_toolbox import Toolbox
from plangrid.flask_toolbox.restful_adapters import RestfulApiAdapter
from plangrid.flask_toolbox.http_errors import BadRequest

class TestRestfulApiAdapter(TestCase):
    def create_app(self):
        app = Flask(__name__)
        Toolbox(app)
        blueprint = Blueprint('test', __name__)
        adapter = RestfulApiAdapter(blueprint)
        adapter.add_resource(SimpleHandler, '/thing', ['GET', 'POST'])
        adapter.add_resource(DictRespondingHandler, '/dict', ['GET'])
        adapter.add_resource(EmptyResponseHandler, '/nothing', ['GET'])
        adapter.add_resource(KwargsHandler, '/exclaim/<string:word>', ['GET'])
        adapter.add_resource(ErrorThrowingHandler, '/error', ['GET'])
        app.register_blueprint(blueprint)
        return app

    def test_http_methods(self):
        resp = self.app.test_client().get('/thing')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.decode('utf-8'), 'hello')

        resp = self.app.test_client().post('/thing')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data.decode('utf-8'), 'goodbye')

        resp = self.app.test_client().delete('/thing')
        self.assertEqual(resp.status_code, 405)

        resp = self.app.test_client().get('/stuff')
        self.assertEqual(resp.status_code, 404)

    def test_dict_response(self):
        resp = self.app.test_client().get('/dict')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, TEST_DICT)

    def test_empty_response(self):
        resp = self.app.test_client().get('/nothing')
        self.assertEqual(resp.data.decode('utf-8'), '')

    def test_kwargs(self):
        resp = self.app.test_client().get('/exclaim/hello')
        self.assertEqual(resp.data.decode('utf-8'), 'hello!')

    def test_error_handler(self):
        resp = self.app.test_client().get('/error')
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, {'message': BadRequest.default_message})

TEST_DICT = {'some': 'stuff', 'in_a': 'dict'}

class SimpleHandler(object):
    def get(self):
        return 'hello', 200
    def post(self):
        return 'goodbye', 201

class DictRespondingHandler(object):
    def get(self):
        return TEST_DICT, 200

class EmptyResponseHandler(object):
    def get(self):
        return None, 204

class KwargsHandler(object):
    def get(self, word):
        return '{}!'.format(word), 200

class ErrorThrowingHandler(object):
    def get(self):
        raise BadRequest()