from __future__ import unicode_literals

import json

from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest as WerkzeugBadRequest
from werkzeug.routing import BaseConverter
from werkzeug.wrappers import Response as WerkzeugResponse

from plangrid.flask_toolbox import messages
from plangrid.flask_toolbox.extension import Extension
from plangrid.flask_toolbox.validation import UUID


class UUIDStringConverter(BaseConverter):
    def to_python(self, value):
        try:
            validated = UUID().deserialize(value)
        except ValidationError:
            # This is happening during routing, before our Flask handlers are
            # invoked, so our normal HttpJsonError objects will not be caught.
            # Instead, we need to raise a Werkzeug error.
            body = json.dumps({'message': messages.invalid_uuid})
            raise WerkzeugBadRequest(
                response=WerkzeugResponse(
                    response=body,
                    status=400,
                    content_type='application/json'
                )
            )
        return validated

    to_url = to_python


class UrlConverters(Extension):
    NAME = 'ToolboxExtension::UrlConverters'

    def init_extension(self, app, config):
        app.url_map.converters['uuid_string'] = UUIDStringConverter
