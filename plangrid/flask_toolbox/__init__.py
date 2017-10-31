from __future__ import unicode_literals

from plangrid.flask_toolbox.toolbox_proxy import (
    toolbox_proxy
)

from plangrid.flask_toolbox.decorators import (
    authenticated,
    scoped
)

from plangrid.flask_toolbox.request_utils import (
    get_header_params_or_400,
    get_query_string_params_or_400,
    get_json_body_params_or_400,
    get_user_id_from_header_or_400,
    marshal,
    response,
    list_response,
    paginated_response,
    verify_scope_or_403,
    scope_app
)

from plangrid.flask_toolbox.toolbox import (
    Toolbox,
    DEFAULT_PAGINATION_LIMIT_MAX,
    HEADER_AUTH_TOKEN,
    HEADER_USER_ID,
    HEADER_REQUEST_ID,
    HEADER_SCOPES,
    HEADER_APPLICATION_ID,
    HEALTHCHECK_ENDPOINT
)

from plangrid.flask_toolbox.framing.framer import (
    Framer
)
from plangrid.flask_toolbox.framing.authenticators import\
    HeaderApiKeyAuthenticator


class ToolboxFramer(Framer):
    def __init__(self, swagger_generator=None):
        authenticator = HeaderApiKeyAuthenticator(header=HEADER_AUTH_TOKEN)
        super(ToolboxFramer, self).__init__(
            default_authenticator=authenticator,
            swagger_generator=swagger_generator,
        )
