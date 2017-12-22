from __future__ import unicode_literals

from flask import Flask
from flask_testing import TestCase

from plangrid.flask_toolbox.pagination.request_utils import paginated_response
from plangrid.flask_toolbox.pagination import Pagination


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
