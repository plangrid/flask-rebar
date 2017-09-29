from __future__ import unicode_literals

import copy
import os
import sys
import uuid
from functools import wraps

import bugsnag
import bugsnag.flask
import marshmallow
from flask import Request
from flask import current_app
from flask import jsonify
from flask import request
from marshmallow import ValidationError
from newrelic import agent as newrelic_agent
from six.moves.urllib.parse import urlencode
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest
from werkzeug.routing import BaseConverter
from werkzeug.security import safe_str_cmp

from plangrid.flask_toolbox import http_errors
from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.toolbox_proxy import toolbox_proxy
from plangrid.flask_toolbox.validation import ObjectId
from plangrid.flask_toolbox.validation import UUID

DEFAULT_PAGINATION_LIMIT_MAX = 100
HEADER_AUTH_TOKEN = 'X-PG-Auth'
HEADER_USER_ID = 'X-PG-UserId'
HEADER_REQUEST_ID = 'X-PG-RequestId'
HEADER_SCOPES = 'X-PG-Scopes'
HEADER_APPLICATION_ID = 'X-PG-AppId'
HEALTHCHECK_ENDPOINT = 'health'


class ToolboxRequest(Request):
    """Lightly wraps flask.Request to getters for PlanGrid specific headers."""
    @property
    def user_id(self):
        return self.headers.get(HEADER_USER_ID)

    @property
    def request_id(self):
        return self.headers.get(HEADER_REQUEST_ID, str(uuid.uuid4()))

    @property
    def auth_token(self):
        return self.headers.get(HEADER_AUTH_TOKEN)

    @property
    def application_id(self):
        return self.headers.get(HEADER_APPLICATION_ID)

    @property
    def scopes(self):
        scopes_string = self.headers.get(HEADER_SCOPES, '').strip()
        if scopes_string:
            scopes_split = [
                s.strip()
                for s in scopes_string.split(' ')
                if s
            ]
            return set(scopes_split)
        else:
            return set()

    def on_json_loading_failed(self, e):
        raise http_errors.BadRequest(messages.invalid_json)


class Toolbox(object):
    """
    Extends a Flask application to become a PlanGrid style REST API.

    :param flask.Flask app:


    Configuration parameters
    ------------------------

    These are retrieved in the following priority order:
    1) If the parameter is passed in on instantiation, that value get's first
       priority,
    2) Otherwise, the application's config object is inspected for the
       parameter.
    3) If the application's config doesn't have it, the environment is
       inspected for the variable.

    :param str base_url: TOOLBOX_BASE_URL
      When generating URLs in responses, this will be used
      as the base of the url (i.e. the schema and hostname).
      For example: 'https://io.plangrid.com'

    :param str auth_token: TOOLBOX_AUTH_TOKEN
      This token is used as a secret shared key with authenticating incoming
      requests (i.e., if a handler is decorated as @authenticated, incoming
      requests will be inspected for the X-PG-Auth header, and that header
      must match this token).

    :param int pagination_limit_max: TOOLBOX_PAGINATION_LIMIT_MAX
      Limit request parameters will default to this value.

    :param str bugsnag_api_key: BUGSNAG_API_KEY
      The API key for the bugsnag integration.

    :param str bugsnag_release_stage: BUGSNAG_RELEASE_STAGE
      Notifications to bugsnag will be namespaced under this release stage.
      Usually this is the "stack" that the application is running in...
      e.g. "dev", "test", or "prod"
    """
    def __init__(
            self,
            app=None,
            base_url=None,
            auth_token=None,
            pagination_limit_max=None,
            bugsnag_api_key=None,
            bugsnag_release_stage=None
    ):
        self.app = app
        self.base_url = base_url
        self.auth_token = auth_token
        self.pagination_limit_max = pagination_limit_max
        self.bugsnag_api_key = bugsnag_api_key
        self.bugsnag_release_stage = bugsnag_release_stage

        if app is not None:
            self.init_app(app)

    @staticmethod
    def _get_config(app, env_var_name, default=None):
        """
        Gets a config variable from either the app.config or the environment
        """
        return app.config.get(env_var_name, os.getenv(env_var_name, default))

    def init_app(self, app):
        self.base_url = (
            self.base_url
            if self.base_url is not None
            else self._get_config(app, 'TOOLBOX_BASE_URL')
        )
        self.auth_token = (
            self.auth_token
            if self.auth_token is not None
            else self._get_config(app, 'TOOLBOX_AUTH_TOKEN')
        )
        self.pagination_limit_max = int(
            self.pagination_limit_max
            if self.pagination_limit_max is not None
            else self._get_config(app, 'TOOLBOX_PAGINATION_LIMIT_MAX',
                                  default=DEFAULT_PAGINATION_LIMIT_MAX)
        )
        self.bugsnag_api_key = (
            self.bugsnag_api_key
            if self.bugsnag_api_key is not None
            else self._get_config(app, 'BUGSNAG_API_KEY')
        )
        self.bugsnag_release_stage = (
            self.bugsnag_release_stage
            if self.bugsnag_release_stage is not None
            else self._get_config(app, 'BUGSNAG_RELEASE_STAGE',
                                  default='production')
        )

        self._register_custom_error_handler(app)
        self._register_werkzeug_error_handler(app)
        self._register_healthcheck(app)
        if self.bugsnag_api_key:
            self._configure_bugsnag(app)
        self._register_custom_converters(app)

        # Set the flask.request proxy to our extended type
        app.request_class = ToolboxRequest

        # Add a reference to this Toolbox instance in the app context
        app.app_ctx_globals_class.toolbox = self

    def _create_json_error_response(
            self,
            message,
            http_status_code,
            error_code=None,
            additional_data=None
    ):
        """
        Compiles a response object for an error.

        :param str message:
        :param int http_status_code:
        :param error_code:
          An optional, application-specific error code to add to the response.
        :param additional_data:
          Additional JSON data to attach to the response.
        :rtype: flask.Response
        """
        body = {'message': message}
        if error_code:
            body['error_code'] = error_code
        if additional_data:
            body.update(additional_data)
        resp = jsonify(body)
        resp.status_code = http_status_code
        return resp

    def _register_custom_error_handler(self, app):
        """Registers an error handler for our flask_toolbox.http_errors."""
        @app.errorhandler(http_errors.HttpJsonError)
        def handle_http_error(error):
            return self._create_json_error_response(
                message=error.error_message,
                http_status_code=error.http_status_code,
                additional_data=error.additional_data
            )

    def _register_werkzeug_error_handler(self, app):
        """Registers handlers to change built-in Flask errors to JSON errors."""
        @app.errorhandler(404)
        @app.errorhandler(405)
        def handle_werkzeug_http_error(error):
            return self._create_json_error_response(
                message=error.description,
                http_status_code=error.code
            )

        @app.errorhandler(Exception)
        def handle_werkzeug_http_error(error):
            exc_info = sys.exc_info()
            current_app.log_exception(exc_info=exc_info)
            bugsnag.notify(error)
            newrelic_agent.record_exception(*exc_info)
            return self._create_json_error_response(
                message=messages.internal_server_error,
                http_status_code=500
            )

    def _register_healthcheck(self, app):
        """Adds a /health endpoint to the application."""
        @app.route('/health', endpoint=HEALTHCHECK_ENDPOINT)
        def handle_healthcheck():
            return jsonify({'message': messages.health_check_response})

    def _configure_bugsnag(self, app):
        """Configures flask to forward uncaught exceptions to Bugsnag."""
        bugsnag.configure(
            api_key=self.bugsnag_api_key,
            release_stage=self.bugsnag_release_stage
        )
        bugsnag.flask.handle_exceptions(app)

    def _register_custom_converters(self, app):
        app.url_map.converters['uuid_string'] = UUIDStringConverter


def scope_app(app, required_scope):
    """
    Extends an application (or blueprint) to only accept requests that
    have the proper scope set in the headers.

    :param flask.Flask|flask.Blueprint app:

    :param str required_scope: 
      The extension will verify that all requests have this scope in the headers
    """

    @app.before_request
    def verify_scope():
        verify_scope_or_403(required_scope=required_scope)


def _make_url(resource_path, query_params):
    """
    Constructs a full URL for the application.

    :param str resource_path: e.g. /path/to/resource
    :param dict query_params: e.g. {'skip': 0, 'limit': 100}
    :return: e.g. https://io.plangrid.com/path/to/resource?skip=0&limit=100
    :rtype: str
    """
    url_params = urlencode(
        [
            (param, value)
            # sorted so testing is more reliable
            for param, value in sorted(query_params.items())
            if value is not None
        ]
    )

    return '{}{}?{}'.format(toolbox_proxy.base_url, resource_path, url_params)


def paginated_response(data, total_count, additional_data=None, status_code=200):
    """
    Constructs a flask.Response for paginated endpoint.

    :param list data: The current page of data to return to the client
    :param int total_count: The total amount of resources matching the query
    :param dict additional_data: Any additional data to attach to the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    resp = {
        'data': data,
        'total_count': total_count,
        'next_page_url': None
    }

    query_params = request.args.to_dict()

    skip = int(query_params.get('skip', 0))
    limit = int(query_params.get('limit', toolbox_proxy.pagination_limit_max))

    if skip + limit < total_count:
        query_params['skip'] = skip + limit
        query_params['limit'] = limit
        resp['next_page_url'] = _make_url(
            resource_path=request.path,
            query_params=query_params
        )

    if additional_data:
        resp.update(additional_data)

    return response(data=resp, status_code=status_code)


def response(data, status_code=200):
    """
    Constructs a flask.Response.

    :param dict data: The JSON body of the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    resp = jsonify(data)
    resp.status_code = status_code
    return resp


def list_response(data, additional_data, status_code=200):
    """
    Constructs a flask.Response for an endpoint that returns a list.

    :param list data:
    :param dict additional_data: Any additional data to attach to the response
    :param int status_code: HTTP status code to use in the response
    :rtype: flask.Response
    """
    resp = {'data': data}
    if additional_data:
        resp.update(additional_data)
    return response(data=resp, status_code=status_code)


def _get_json_body_or_400():
    """
    Retrieves the JSON payload of the current request, throwing a 400 error
    if the request doesn't include a valid JSON payload.
    """
    if 'application/json' not in request.headers.get('content-type', ''):
        raise http_errors.BadRequest(messages.unsupported_content_type)

    if (not request.data) or (len(request.data) == 0):
        raise http_errors.BadRequest(messages.empty_json_body)

    # JSON decoding errors will be handled in ToolboxRequest.on_json_loading_failed
    body = request.get_json()

    if not isinstance(body, list) and not isinstance(body, dict):
        # request.get_json() treats strings as valid JSON, which is technically
        # true... but they're not valid objects. So let's throw an error on
        # primitive types.
        raise http_errors.BadRequest(messages.invalid_json)

    return body


def _format_marshmallow_errors_for_response_in_place(errs):
    """
    Reformats an error dictionary returned by marshmallow to an error
    dictionary we can send in a response.

    This transformation happens in place, so make sure to pass in a copy
    of the errors...
    """
    # These are errors on the entire schema, not a specific field
    # Let's rename these too something slightly less cryptic
    if '_schema' in errs:
        errs['_general'] = errs.pop('_schema')

    for field, value in errs.items():
        # In most cases we'll only have a single error for a field,
        # but marshmallow gives us a list regardless.
        # Let's try to reduce the complexity of the error response and convert
        # these lists to a single string.
        if isinstance(value, list) and len(value) == 1:
            errs[field] = value[0]
        elif isinstance(value, dict):
            # Recurse! Down the rabbit hole...
            _format_marshmallow_errors_for_response_in_place(value)


def _raise_400_for_marshmallow_errors(errs, msg):
    """
    Throws a 400 error properly formatted from the given marshmallow errors.

    :param dict errs: Error dictionary as returned by marshmallow
    :param str msg: The overall message to use in the response.
    :raises: http_errors.BadRequest
    """
    if not errs:
        return

    copied = copy.deepcopy(errs)

    _format_marshmallow_errors_for_response_in_place(copied)

    additional_data = {'errors': copied}

    raise http_errors.BadRequest(
        msg=msg,
        additional_data=additional_data,
    )


def _normalize_schema(schema):
    """
    This allows for either an instance of a marshmallow.Schema or the class
    itself to be passed to functions.
    """
    if not isinstance(schema, marshmallow.Schema):
        return schema()
    else:
        return schema


def get_json_body_params_or_400(schema):
    """
    Retrieves the JSON body of a request, validating/loading the payload
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    body = _get_json_body_or_400()

    schema = _normalize_schema(schema)

    json_body_params, errs = schema.load(data=body)

    if errs:
        _raise_400_for_marshmallow_errors(
            errs=errs,
            msg=messages.body_validation_failed
        )

    return json_body_params


def get_query_string_params_or_400(schema):
    """
    Retrieves the query string of a request, validating/loading the parameters
    with a given marshmallow.Schema.

    :param schema:
    :rtype: dict
    """
    query_multidict = request.args.copy()

    schema = _normalize_schema(schema)

    # Deliberately use the request.args MultiDict in case a validator wants to
    # do something with several of the same query param (e.g. ?foo=1&foo=2), in
    # which case it will need the getlist method
    query_string_params, errs = schema.load(data=query_multidict)

    if errs:
        _raise_400_for_marshmallow_errors(
            errs=errs,
            msg=messages.query_string_validation_failed
        )

    return query_string_params


def get_user_id_from_header_or_400():
    """
    Retrieves the user ID from the header of a request, validating it as an
    ObjectID and raising a 400 error if it is missing or invalid.

    :rtype: str
    """
    user_id = request.user_id
    if not user_id:
        raise http_errors.BadRequest(msg=messages.missing_user_id)

    try:
        ObjectId().deserialize(value=user_id)
    except marshmallow.ValidationError:
        raise http_errors.BadRequest(msg=messages.invalid_user_id)

    return user_id


def verify_scope_or_403(required_scope):
    """
    Verifies that the given scope is included in the request headers. If it
    isn't, this will raise a 403 error.

    :param str required_scope:
    :raises: https_errors.Forbidden 
    """
    if required_scope not in request.scopes:
        raise http_errors.Forbidden(messages.missing_required_scope)


def marshal(data, schema):
    """
    Dumps an object with the given marshmallow.Schema.

    :raises: marshmallow.ValidationError if the given data fails validation
      of the schema.
    """
    schema = _normalize_schema(schema)
    schema.strict = True
    return schema.dump(data).data


def authenticated(handler):
    """
    Verifies that the request to the target endpoint is authenticated.

    Authentication currently happens via a shared token.
    A user id is also required to be sent in via the header to give an
    authorization context for the handler.
    """
    @wraps(handler)
    def wrapper(*args, **kwargs):
        token = request.auth_token

        if not token:
            raise http_errors.Unauthorized(messages.missing_auth_token)

        elif not safe_str_cmp(str(token), toolbox_proxy.auth_token):
            raise http_errors.Unauthorized(messages.invalid_auth_token)

        user_id = request.user_id

        if not user_id:
            raise http_errors.Unauthorized(messages.missing_user_id)

        bugsnag.configure_request(user={"id": user_id})
        newrelic_agent.add_custom_parameter('userId', user_id)

        return handler(*args, **kwargs)

    return wrapper


def scoped(required_scope):
    """
    Verifies that the request to the target endpoint has the proper scope.
    
    Scope is included as a space separated list in a header.
    
    :param str required_scope: The scope required to access this resource 
    """
    def decorator(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            verify_scope_or_403(required_scope=required_scope)

            return handler(*args, **kwargs)

        return wrapper

    return decorator


class UUIDStringConverter(BaseConverter):
    def to_python(self, value):
        try:
            validated = UUID().deserialize(value)
        except ValidationError:
            # This is happening during routing, before our Flask handlers are
            # invoked, so our normal HttpJsonError objects will not be caught.
            # Instead, we need to raise a Werkzeug error.
            raise WerkzeugBadRequest(
                response=response({'message': messages.invalid_uuid}, 400)
            )
        return validated

    to_url = to_python
