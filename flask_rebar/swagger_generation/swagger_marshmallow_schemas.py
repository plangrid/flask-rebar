"""
Probably not gonna use this file but not gonna delete it til I'm sure
"""


from marshmallow import Schema
from marshmallow.fields import Boolean
from marshmallow.fields import Dict
from marshmallow.fields import List
from marshmallow.fields import Nested
from marshmallow.fields import String


class Reference(Schema):
    ref = String()

###


class Contact(Schema):
    name = String()
    url = String()
    email = String()


class License(Schema):
    name = String(required=True)
    url = String()


class Info(Schema):
    title = String(required=True)
    description = String()
    terms_of_service = String()
    contact = Nested(Contact())
    license = Nested(License())
    version = String()

###


class ServerVariable(Schema):
    enum = List(String())
    default = String()
    description = String()


class Server(Schema):
    url = String(required=True)
    description = String()
    variables = Dict(keys=String(), values=List(Nested(ServerVariable())))

###


class ExternalDocumentation(Schema):
    url = String(required=True)
    description = String()


class Schema_(Reference):
    name = String(required=True)


class Parameter(Reference):
    name = String(required=True)
    in_ = String(required=True)
    description = String()
    required = Boolean()
    deprecated = Boolean()
    allow_empty_value = Boolean()
    style = String()
    explode = Boolean()
    allow_reserved = Boolean()
    schema = Schema_()


class Header(Reference):
    description = String()
    required = Boolean()
    deprecated = Boolean()
    allow_empty_value = Boolean()
    style = String()
    explode = Boolean()
    allow_reserved = Boolean()
    schema = Schema_()


class Encoding(Schema):
    content_type = String()
    headers = Dict(keys=String(), values=Nested(Header()))
    style = String()
    explode = Boolean()
    allow_reserved = Boolean()


class MediaType(Schema):
    schema = Nested(Schema_())
    encoding = Dict(keys=String(), values=Nested(Encoding()))


class RequestBody(Reference):
    description = String()
    content = Dict(keys=String(), values=Nested(MediaType()))
    required = Boolean()


class Link(Reference):
    operation_ref = String()
    operation_id = String()
    parameters = Dict(keys=String(), values=String())  # ANY really?
    request_body = String()  # ANY really?
    description = String()
    server = Nested(Server())


class Response(Reference):
    description = String()
    headers = Dict(keys=String(), values=Nested(Header()))
    content = Dict(keys=String(), values=Nested(MediaType()))
    links = Dict(keys=String(), values=Nested(Link()))


class Callback(Reference):
    # ignoring for now
    pass


class SecurityRequirement(Schema):
    # TODO
    pass


class Operation(Schema):
    tags = List(String())
    summary = String()
    description = String()
    external_docs = Nested(ExternalDocumentation())
    operation_id = String()
    parameters = List(Nested(Parameter()))
    request_body = Nested(RequestBody())
    responses = Dict(keys=String(), values=Nested(Response()))
    callbacks = Dict(keys=String(), values=Nested(Callback()))
    deprecated = Boolean()
    security = List(Nested(SecurityRequirement()))
    servers = List(Nested(Server()))


class PathItem(Schema):
    ref = String()
    summary = String()
    description = String()
    get = Nested(Operation())
    put = Nested(Operation())
    post = Nested(Operation())
    delete = Nested(Operation())
    options = Nested(Operation())
    head = Nested(Operation())
    patch = Nested(Operation())
    trace = Nested(Operation())
    servers = List(Nested(Server()))
    parameters = List(Nested(Parameter()))

###


class OAuthFlow(Schema):
    authorization_url = String(required=True)
    token_url = String(required=True)
    refresh_url = String()
    scopes = Dict(keys=String(), values=String(), required=True)


class OAuthFlows(Schema):
    implicit = Nested(OAuthFlow())
    password = Nested(OAuthFlow())
    client_credentials = Nested(OAuthFlow())
    authorization_code = Nested(OAuthFlow())


class SecurityScheme(Reference):
    type = String()
    description = String()
    name = String()
    in_ = String()
    scheme = String()
    bearer_format = String()
    flows = Nested(OAuthFlows())
    open_id_connect_url = String()


class Components(Schema):
    schemas = Dict(keys=String(), values=Nested(Schema_()))
    responses = Dict(keys=String(), values=Nested(Response()))
    parameters = Dict(keys=String(), values=Nested(Parameter()))
    request_bodies = Dict(keys=String(), values=Nested(RequestBody()))
    headers = Dict(keys=String(), values=Nested(Header()))
    security_schemes = Dict(keys=String(), values=Nested(SecurityScheme()))
    links = Dict(keys=String(), values=Nested(Schema_()))
    callbacks = Dict(keys=String(), values=Nested(Schema_()))


class Tag(Schema):
    name = String(required=True)
    description = String()
    external_docs = Nested(ExternalDocumentation())


class OpenAPI(Schema):
    openapi = String(required=True)
    info = Nested(Info(), required=True)
    servers = List(Nested(Server()))
    paths = Dict(keys=String(), values=PathItem(), required=True)
    components = Nested(Components())
    security = List(Nested(SecurityRequirement()))
    tags = List(Nested(Tag()))
    external_docs = Nested(ExternalDocumentation())
