from __future__ import unicode_literals

from flask import Flask
from flask_testing import TestCase

from plangrid.flask_toolbox import http_errors
from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.extensions.errors import Errors


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

        Errors(app)

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
        self.assertEqual(resp.json, {'message': messages.internal_server_error})
