import abc
import copy
import unittest

import marshmallow as m
from werkzeug.security import safe_str_cmp

import re
import json
from flask_testing import TestCase
from collections import defaultdict, namedtuple
from functools import wraps, reduce
from flask import Flask, Blueprint, request
from plangrid.flask_toolbox import get_query_string_params_or_400
from plangrid.flask_toolbox import get_json_body_params_or_400
from plangrid.flask_toolbox import get_header_params_or_400
from plangrid.flask_toolbox import marshal
from plangrid.flask_toolbox import response
from plangrid.flask_toolbox import http_errors
from plangrid.flask_toolbox import Toolbox
from plangrid.flask_toolbox.framing import swagger_words as sw
from plangrid.flask_toolbox.http_errors import BadRequest
from plangrid.flask_toolbox.messages import missing_header_parameter
from plangrid.flask_toolbox import messages


PathDefinition = namedtuple('PathDefinition', [
    'func',
    'path',
    'method',
    'marshal',
    'query_string',
    'request_body',
    'headers',
    'authenticate'
])


ErrorHandlerDefinition = namedtuple('ErrorHandlerDefinition', [
    'code_or_exception',
    'func',
    'schema'
])


USE_DEFAULT = object()


class Authenticator(abc.ABC):
    # @abc.abstractmethod
    # @property
    # def type(self):
    #     pass

    @abc.abstractmethod
    def authenticate(self):
        pass

#
# class ApiKeyAuthenticator(Authenticator):
#
#     def __init__(self, name):
#         self.name = name
#     @property
#     def type(self):
#         return sw.api_key
#
#


class HeaderApiKeyAuthenticator(Authenticator):
    def __init__(self, header, name='sharedSecret'):
        self.header = header
        self.keys = {}
        self.name = name

    # @property
    # def type(self):
    #     return sw.api_key

    def register_key(self, app_name, key):
        self.keys[key] = app_name

    def authenticate(self):
        if self.header not in request.headers:
            raise http_errors.Unauthorized(messages.missing_auth_token)

        token = request.headers[self.header]

        for key, app_name in self.keys.items():
            if safe_str_cmp(str(token), key):
                setattr(request, 'authenticated_app_name', app_name)
                break
        else:

            raise http_errors.Unauthorized(messages.invalid_auth_token)

#
#
# class AbstractParameter(abc.ABC):
#     @abc.abstractmethod
#     def retrieve(self):
#         pass
#
#
# class RequestBody(AbstractParameter):
#     def __init__(self, schema):
#         self.schema = schema
#
#     def retrieve(self):
#         data = get_json_body_params_or_400(self.schema)
#         setattr(request, 'validated_body', data)
#
#
# class QueryString(AbstractParameter):
#     def __init__(self, schema):
#         self.schema = schema
#
#     def retrieve(self):
#         data = get_query_string_params_or_400(self.schema)
#         setattr(request, 'validated_args', data)
#
#
# class Header(AbstractParameter):
#     def __init__(
#             self,
#             name,
#             dest,
#             required=False,
#             default=None
#     ):
#         self.name = name
#         self.dest = dest
#         self.required = required
#         self.default = default
#
#     def retrieve(self):
#         if not self.in_header() and not self.default and self.required:
#             self.on_required_but_missing()
#
#         elif not self.in_header():
#             val = self.get_default()
#             self.set_value(val)
#
#         elif self.in_header():
#             val = request.headers[self.name]
#             self.set_value(val)
#
#     def get_default(self):
#         return self.default() if callable(self.default) else self.default
#
#     def in_header(self):
#         return self.name in request.headers
#
#     def set_value(self, val):
#         setattr(request, self.dest, val)
#
#     def on_required_but_missing(self):
#         raise BadRequest(missing_header_parameter(self.name))
#
#
# class UserIdHeaderParam(Header):
#     def set_value(self, val):
#         super(UserIdHeaderParam, self).set_value(val)


def _wrap_handler(f, definition):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if definition.authenticate:
            definition.authenticate.authenticate()

        if definition.query_string:
            request.validated_args = get_query_string_params_or_400(
                schema=definition.query_string
            )

        if definition.request_body:
            request.validated_body = get_json_body_params_or_400(
                schema=definition.request_body
            )

        if definition.headers:
            request.validated_headers = get_header_params_or_400(
                schema=definition.headers
            )

        rv = f(*args, **kwargs)

        if definition.marshal:
            if isinstance(rv, tuple):
                data, status_code = rv[0], rv[1]
            else:
                data, status_code = rv, 200

            try:
                marshal_schema = definition.marshal[status_code]
            except KeyError:
                raise

            marshaled = marshal(
                data=data,
                schema=marshal_schema
            )

            return response(
                data=marshaled,
                status_code=status_code
            )

        else:
            return rv

    return wrapped


# def _wrap_error_handler(f, schema):
#     @wraps(f)
#     def wrapped(error):
#         data, status_code = f(error)
#
#         marshaled = marshal(
#             data=data,
#             schema=schema
#         )
#
#         return response(
#             data=marshaled,
#             status_code=status_code
#         )
#
#     return wrapped


class Framer(object):
    def __init__(self):
        self.paths = defaultdict(dict)
        self.error_handlers = []
        self.definitions = {}
        self.authenticators = {}

    def add_global_parameter(self):
        pass

    def add_handler(
            self,
            func,
            path,
            method,
            marshal=None,
            query_string=None,
            request_body=None,
            headers=None,
            authenticate=None
    ):
        # TODO: support multiple paths
        self.paths[path][method] = PathDefinition(
            func=func,
            path=path,
            method=method,
            marshal=marshal,
            query_string=query_string,
            request_body=request_body,
            headers=headers,
            authenticate=authenticate
        )

    def handles(
            self,
            path,
            method,
            marshal=None,
            query_string=None,
            request_body=None,
            headers=None,
            authenticate=None
    ):
        def wrapper(f):
            self.add_handler(
                func=f,
                path=path,
                method=method,
                marshal=marshal,
                query_string=query_string,
                request_body=request_body,
                headers=headers,
                authenticate=authenticate
            )
            return f
        return wrapper

    # def add_error_handler(
    #         self,
    #         func,
    #         code_or_exception,
    #         schema
    # ):
    #     self.error_handlers.append(
    #         ErrorHandlerDefinition(
    #             code_or_exception=code_or_exception,
    #             func=func,
    #             schema=schema
    #         )
    #     )
    #
    # def handles_error(self, code_or_exception, schema):
    #     def wrapper(f):
    #         self.add_error_handler(
    #             func=f,
    #             code_or_exception=code_or_exception,
    #             schema=schema
    #         )
    #         return f
    #     return wrapper

    def register(self, app):
        """

        :param flask.Flask app:
        :return:
        """

        for path, methods in self.paths.items():
            for method, definition_ in methods.items():
                app.add_url_rule(
                    rule=definition_.path,
                    view_func=_wrap_handler(definition_.func, definition_),
                    methods=[definition_.method]
                )

        # for definition_ in self.error_handlers:
        #     app.register_error_handler(
        #         code_or_exception=definition_.code_or_exception,
        #         f=_wrap_error_handler(definition_.func, definition_.schema)
        #     )
