from __future__ import unicode_literals

import unittest

from flask import Flask
from flask_testing import TestCase
from marshmallow import Schema

from plangrid.flask_toolbox import Skip, messages, Limit, Pagination, paginated_response


class TestPagination(TestCase):
    PAGINATION_LIMIT_MAX = 100
    BASE_URL = 'http://localhost'

    def create_app(self):
        app = Flask(__name__)
        Pagination(
            app=app,
            config={
                'TOOLBOX_PAGINATION_LIMIT_MAX': self.PAGINATION_LIMIT_MAX
            }
        )

        return app

    def test_paginated_response(self):
        data = [{'foo': 'bar'}]*100
        total_count = len(data)*2

        @self.app.route('/paginated_response')
        def handler():
            return paginated_response(
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
            return paginated_response(
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


class ObjectWithSkip(Schema):
    skip = Skip()


class TestSkip(unittest.TestCase):
    def test_deserialize(self):
        data, _ = ObjectWithSkip().load({'skip': 40})
        self.assertEqual(data['skip'], 40)

        # Works with strings
        data, _ = ObjectWithSkip().load({'skip': '40'})
        self.assertEqual(data['skip'], 40)

        # Skip defaults to 0
        data, _ = ObjectWithSkip().load({})
        self.assertEqual(data['skip'], 0)

    def test_serialize(self):
        data, _ = ObjectWithSkip().dump({'skip': 40})
        self.assertEqual(data['skip'], 40)

        # Skip defaults to 0
        data, _ = ObjectWithSkip().dump({})
        self.assertEqual(data['skip'], 0)

    def test_deserialize_errors(self):
        _, errs = ObjectWithSkip().load({'skip': -1})
        self.assertEqual(errs['skip'], [messages.invalid_skip_value])

    def test_serialize_errors(self):
        _, errs = ObjectWithSkip().dump({'skip': 'hello'})
        self.assertEqual(errs['skip'], [messages.invalid_skip_value])


class ObjectWithLimit(Schema):
    limit = Limit()


class TestLimit(TestCase):
    PAGINATION_LIMIT_MAX = 100

    def create_app(self):
        # We need to initialize an app so we can get the default limit
        app = Flask(__name__)
        Pagination(
            app=app,
            config={
                'TOOLBOX_PAGINATION_LIMIT_MAX': self.PAGINATION_LIMIT_MAX
            }
        )
        return app

    def test_deserialize(self):
        with self.app.test_request_context():
            # We need to do with so "before_request" callbacks are called
            self.app.preprocess_request()

            data, _ = ObjectWithLimit().load({'limit': 50})
            self.assertEqual(data['limit'], 50)

            # Works with strings
            data, _ = ObjectWithLimit().load({'limit': '50'})
            self.assertEqual(data['limit'], 50)

            # Limit defaults to the toolbox's default
            data, _ = ObjectWithLimit().load({})
            self.assertEqual(data['limit'], self.PAGINATION_LIMIT_MAX)

            class ObjectWithNullDefaultLimit(Schema):
                limit = Limit(default=None)

            # Limit can be made none
            data, _ = ObjectWithNullDefaultLimit().load({})
            self.assertIsNone(data['limit'])

    def test_serialize(self):
        data, _ = ObjectWithLimit().dump({'limit': 50})
        self.assertEqual(data['limit'], 50)

    def test_deserialize_errors(self):
        with self.app.test_request_context():
            # We need to do with so "before_request" callbacks are called
            self.app.preprocess_request()

            _, errs = ObjectWithLimit().load({'limit': 0})
            self.assertEqual(errs['limit'], [messages.invalid_limit_value])

            _, errs = ObjectWithLimit().load({'limit': self.PAGINATION_LIMIT_MAX + 1})
            self.assertEqual(errs['limit'], [messages.limit_over_max(self.PAGINATION_LIMIT_MAX)])

    def test_serialize_errors(self):
        _, errs = ObjectWithLimit().dump({'limit': 'hello'})
        self.assertEqual(errs['limit'], [messages.invalid_limit_value])
