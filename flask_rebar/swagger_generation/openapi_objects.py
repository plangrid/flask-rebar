from abc import abstractmethod

from flask_rebar.swagger_generation import swagger_words as sw


class SwaggerObject:
    """Base class for a Swagger object"""

    def __getitem__(self, attr):
        """Allow dict-like access for compatibility"""
        return self.__getattribute__(attr)

    @abstractmethod
    def as_swagger(self):
        """Create a Swagger representation of this object

        :rtype: dict
        """
        raise NotImplementedError()


class DictSetMixin:
    def __setitem__(self, key, value):
        self.__setattr__(key, value)


class Reference(SwaggerObject):
    """Represents a Swagger "Reference Object"

    :param str ref: A reference other components in the spec. e.g. "$ref": "#/components/schemas/Pet"
    """
    def __init__(self, ref):
        self.ref = ref

    def as_swagger(self):
        doc = {sw.ref: self.ref}
        return doc


class Contact(SwaggerObject):
    """Represents a Swagger "Contact Object"

    :param str name: The identifying name of the contact person/organization.
    :param str url: The URL pointing to the contact information. MUST be in the format of a URL.
    :param str email: The email address of the contact person/organization. MUST be in the format of an email address.
    """

    def __init__(self, name=None, url=None, email=None):
        self.name = name
        self.url = url
        self.email = email

    def as_swagger(self):
        doc = {}
        if self.name:
            doc[sw.name] = self.name
        if self.url:
            doc[sw.url] = self.url
        if self.email:
            doc[sw.email] = self.email
        return doc


class License(SwaggerObject):
    """Represents a Swagger "License Object"

    :param str name: REQUIRED. The license name used for the API.
    :param str url: A URL to the license used for the API. MUST be in the format of a URL.
    """

    def __init__(self, name, url=None):
        self.name = name
        self.url = url

    def as_swagger(self):
        doc = {sw.name: self.name}
        if self.url:
            doc[sw.url] = self.url
        return doc


class Info(SwaggerObject):
    """Represents a Swagger "Info Object"

    :param str title: REQUIRED. The title of the application.
    :param str description: A short description of the application. CommonMark syntax MAY be used for rich text representation.
    :param str terms_of_service: A URL to the Terms of Service for the API. MUST be in the format of a URL.
    :param Contact contact: The contact information for the exposed API.
    :param License license: The license information for the exposed API.
    :param str version: REQUIRED. The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API implementation version).
    """

    def __init__(self, title, version, description=None, terms_of_service=None, contact=None, license=None):
        self.title = title
        self.description = description
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license = license
        self.version = version

    def as_swagger(self):
        doc = {
            sw.title: self.title,
            sw.version: self.version,
        }
        if self.description:
            doc[sw.description] = self.description
        if self.terms_of_service:
            doc[sw.terms_of_service] = self.terms_of_service
        if self.contact:
            doc[sw.contact] = self.contact.as_swagger()
        if self.license:
            doc[sw.license_] = self.license.as_swagger()
        return doc


class ExternalDocumentation(SwaggerObject):
    """Represents a Swagger "External Documentation Object"

    :param str url: The URL for the target documentation. Value MUST be in the format of a URL
    :param str description: A short description of the target documentation
    """
    def __init__(self, url, description=None):
        self.url = url
        self.description = description

    def as_swagger(self):
        doc = {sw.url: self.url}
        if self.description:
            doc[sw.description] = self.description
        return doc


class Tag(SwaggerObject):
    """Represents a Swagger "Tag Object"

    :param str name: The name of the tag
    :param str description: A short description for the tag
    :param ExternalDocumentation external_docs: Additional external documentation for this tag
    """
    def __init__(self, name, description=None, external_docs=None):
        self.name = name
        self.description = description
        self.external_docs = external_docs

    def as_swagger(self):
        doc = {sw.name: self.name}
        if self.description:
            doc[sw.description] = self.description
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs.as_swagger()
        return doc


class ServerVariable(SwaggerObject):
    """Represents a Swagger "Server Variable Object"

    :param list[str] enum: An enumeration of string values to be used if the substitution options are from a limited set.
    :param str default: REQUIRED. The default value to use for substitution, which SHALL be sent if an alternate value is not supplied. Note this behavior is different than the Schema Object's treatment of default values, because in those cases parameter values are optional.
    :param str description: An optional description for the server variable. CommonMark syntax MAY be used for rich text representation.
    """

    def __init__(
            self,
            default,
            enum=None, description=None,
    ):
        self.enum = enum
        self.default = default
        self.description = description

    def as_swagger(self):
        doc = {sw.default: self.default}
        if self.enum:
            doc[sw.enum] = self.enum
        if self.description:
            doc[sw.description] = self.description
        return doc


class Server(SwaggerObject):
    """Represents a Swagger "Server Object"

    :param str url: REQUIRED. A URL to the target host. This URL supports Server Variables and MAY be relative, to indicate that the host location is relative to the location where the OpenAPI document is being served. Variable substitutions will be made when a variable is named in {brackets}.
    :param str description: An optional string describing the host designated by the URL. CommonMark syntax MAY be used for rich text representation.
    :param dict[str, ServerVariable] variables: A map between a variable name and its value. The value is used for substitution in the server's URL template.
    """

    def __init__(
            self,
            url,
            description=None, variables=None,
    ):
        self.url = url
        self.description = description
        self.variables = variables

    def as_swagger(self):
        doc = {sw.url: self.url}
        if self.description:
            doc[sw.description] = self.description
        if self.variables:
            doc[sw.variables] = {k: v.as_swagger() for k, v in self.variables}
        return doc


class Header(SwaggerObject):
    """Represents a Swagger "Header Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        doc = {}
        return doc


class MediaType(SwaggerObject):
    """Represents a Swagger "MediaType Object"

    :param Schema or Reference schema: The schema defining the content of the request, response, or parameter.
    :param Example example: Example of the media type. The example object SHOULD be in the correct format as specified by the media type. The example field is mutually exclusive of the examples field. Furthermore, if referencing a schema which contains an example, the example value SHALL override the example provided by the schema.
    :param dict[str, Example or Reference] examples: Examples of the media type. Each example object SHOULD match the media type and specified schema if present. The examples field is mutually exclusive of the example field. Furthermore, if referencing a schema which contains an example, the examples value SHALL override the example provided by the schema.
    :param dict[str, Encoding] encoding: A map between a property name and its encoding information. The key, being the property name, MUST exist in the schema as a property. The encoding object SHALL only apply to requestBody objects when the media type is multipart or application/x-www-form-urlencoded.
    """

    def __init__(self, schema=None, example=None, examples=None, encoding=None):
        self.schema = schema
        self.example = example
        self.examples = examples
        self.encoding = encoding

    def as_swagger(self):
        doc = {}
        if self.schema:
            doc[sw.schema] = self.schema.as_swagger()
        if self.example:
            doc[sw.example] = self.example.as_swagger()
        if self.examples:
            doc[sw.examples] = {k: v.as_swagger() for k, v in self.examples.items()}
        if self.encoding:
            doc[sw.encoding] = {k: v.as_swagger() for k, v in self.encoding.items()}
        return doc


class Link(SwaggerObject):
    """Represents a Swagger "Link Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        doc = {}
        return doc


class Response(SwaggerObject):
    """Represents a Swagger "Response Object"

    :param str description: REQUIRED. A short description of the response. CommonMark syntax MAY be used for rich text representation.
    :param dict[str, Header or Reference] headers: Maps a header name to its definition. RFC7230 states header names are case insensitive. If a response header is defined with the name "Content-Type", it SHALL be ignored.
    :param dict[str, MediaType or Reference] content: A map containing descriptions of potential response payloads. The key is a media type or media type range and the value describes it. For responses that match multiple keys, only the most specific key is applicable. e.g. text/plain overrides text/*
    :param dict[str, Link or Reference] links: A map of operations links that can be followed from the response. The key of the map is a short name for the link, following the naming constraints of the names for Component Objects.
    """

    def __init__(
            self,
            description,
            headers=None, content=None, links=None,
    ):
        self.description = description
        self.headers = headers
        self.content = content
        self.links = links

    def as_swagger(self):
        doc = {sw.description: self.description}
        if self.headers:
            doc[sw.headers] = {k: v.as_swagger() for k, v in self.headers.items()}
        if self.content:
            doc[sw.content] = {k: v.as_swagger() for k, v in self.content.items()}
        if self.links:
            doc[sw.links] = {k: v.as_swagger() for k, v in self.links.items()}
        return doc


class Operation(SwaggerObject):
    """Represents a Swagger "Operation Object"

    :param list[str] tags: A list of tags for API documentation control. Tags can be used for logical grouping of operations by resources or any other qualifier.
    :param str summary: A short summary of what the operation does.
    :param str description: A verbose explanation of the operation behavior. CommonMark syntax MAY be used for rich text representation.
    :param ExternalDocs external_docs: Additional external documentation for this operation.
    :param str operation_id: Unique string used to identify the operation. The id MUST be unique among all operations described in the API. The operationId value is case-sensitive. Tools and libraries MAY use the operationId to uniquely identify an operation, therefore, it is RECOMMENDED to follow common programming naming conventions.
    :param list[Parameter or Reference] parameters: A list of parameters that are applicable for this operation. If a parameter is already defined at the Path Item, the new definition will override it but can never remove it. The list MUST NOT include duplicated parameters. A unique parameter is defined by a combination of a name and location. The list can use the Reference Object to link to parameters that are defined at the OpenAPI Object's components/parameters.
    :param RequestBody or Reference request_body: The request body applicable for this operation. The requestBody is only supported in HTTP methods where the HTTP 1.1 specification RFC7231 has explicitly defined semantics for request bodies. In other cases where the HTTP spec is vague, requestBody SHALL be ignored by consumers.
    :param dict[str, Response or Reference] responses: REQUIRED. The list of possible responses as they are returned from executing this operation.
        default: The documentation of responses other than the ones declared for specific HTTP response codes. Use this field to cover undeclared responses. A Reference Object can link to a response that the OpenAPI Object's components/responses section defines.
        HTTP Status Code: Any HTTP status code can be used as the property name, but only one property per code, to describe the expected response for that HTTP status code. A Reference Object can link to a response that is defined in the OpenAPI Object's components/responses section. This field MUST be enclosed in quotation marks (for example, "200") for compatibility between JSON and YAML. To define a range of response codes, this field MAY contain the uppercase wildcard character X. For example, 2XX represents all response codes between [200-299]. Only the following range definitions are allowed: 1XX, 2XX, 3XX, 4XX, and 5XX. If a response is defined using an explicit code, the explicit code definition takes precedence over the range definition for that code.
    :param dict[str, Callback or Reference] callbacks: A map of possible out-of band callbacks related to the parent operation. The key is a unique identifier for the Callback Object. Each value in the map is a Callback Object that describes a request that may be initiated by the API provider and the expected responses. The key value used to identify the callback object is an expression, evaluated at runtime, that identifies a URL to use for the callback operation.
    :param bool deprecated: Declares this operation to be deprecated. Consumers SHOULD refrain from usage of the declared operation. Default value is false.
    :param list[SecurityRequirement] security: A declaration of which security mechanisms can be used for this operation. The list of values includes alternative security requirement objects that can be used. Only one of the security requirement objects need to be satisfied to authorize a request. This definition overrides any declared top-level security. To remove a top-level security declaration, an empty array can be used.
    :param list[Server]	servers: An alternative server array to service this operation. If an alternative server object is specified at the Path Item Object or Root level, it will be overridden by this value.
    """

    def __init__(
            self,
            responses,
            tags=None, summary=None, description=None, external_docs=None, operation_id=None, parameters=None, request_body=None, callbacks=None, deprecated=None, security=None, servers=None,
    ):
        self.responses = responses

        self.tags = tags
        self.summary = summary
        self.description = description
        self.external_docs = external_docs
        self.operation_id = operation_id
        self.parameters = parameters
        self.request_body = request_body
        self.callbacks = callbacks
        self.deprecated = deprecated
        self.security = security
        self.servers = servers

    def as_swagger(self):
        doc = {
            sw.responses: {k: v.as_swagger() for k, v in self.responses.items()}
        }
        if self.tags:
            doc[sw.tags] = self.tags
        if self.summary:
            doc[sw.summary] = self.summary
        if self.description:
            doc[sw.description] = self.description
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs.as_swagger()
        if self.operation_id:
            doc[sw.operation_id] = self.operation_id
        if self.parameters:
            doc[sw.parameters] = [i.as_swagger() for i in self.parameters]
        if self.request_body:
            doc[sw.request_body] = self.request_body.as_swagger()
        if self.callbacks:
            doc[sw.callbacks] = {k: v.as_swagger() for k, v in self.callbacks.items()}
        if self.deprecated:
            doc[sw.deprecated] = self.deprecated
        if self.security is not None:  # see docstring
            doc[sw.security] = [i.as_swagger() for i in self.security]
        if self.servers:
            doc[sw.servers] = [i.as_swagger() for i in self.servers]
        return doc


class Schema(SwaggerObject):
    """Represents a Swagger "Schema Object"

    The following properties are taken directly from the JSON Schema definition and follow the same specifications:
    :param title
    :param multiple_of
    :param maximum
    :param exclusive_maximum
    :param minimum
    :param exclusive_minimum
    :param max_length
    :param min_length
    :param pattern
    :param max_items
    :param min_items
    :param unique_items
    :param max_properties
    :param min_properties
    :param required
    :param enum

    The following properties are taken from the JSON Schema definition but their definitions were adjusted to the OpenAPI Specification.
    :param type_ - Value MUST be a string. Multiple types via an array are not supported.
    :param all_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    :param one_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    :param any_of - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    :param not_ - Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema.
    :param items - Value MUST be an object and not an array. Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema. items MUST be present if the type is array.
    :param properties - Property definitions MUST be a Schema Object and not a standard JSON Schema (inline or referenced).
    :param additional_properties - Value can be boolean or object. Inline or referenced schema MUST be of a Schema Object and not a standard JSON Schema. Consistent with JSON Schema, additionalProperties defaults to true.
    :param description - CommonMark syntax MAY be used for rich text representation.
    :param format_ - See Data Type Formats for further details. While relying on JSON Schema's defined formats, the OAS offers a few additional predefined formats.
    :param default - The default value represents what would be assumed by the consumer of the input as the value of the schema if one is not provided. Unlike JSON Schema, the value MUST conform to the defined type for the Schema Object defined at the same level. For example, if type is string, then default can be "foo" but cannot be 1.

    :param bool nullable: Allows sending a null value for the defined schema. Default value is false.
    :param Discriminator discriminator: Adds support for polymorphism. The discriminator is an object name that is used to differentiate between other schemas which may satisfy the payload description. See Composition and Inheritance for more details.
    :param bool readOnly: Relevant only for Schema "properties" definitions. Declares the property as "read only". This means that it MAY be sent as part of a response but SHOULD NOT be sent as part of the request. If the property is marked as readOnly being true and is in the required list, the required will take effect on the response only. A property MUST NOT be marked as both readOnly and writeOnly being true. Default value is false.
    :param bool writeOnly: Relevant only for Schema "properties" definitions. Declares the property as "write only". Therefore, it MAY be sent as part of a request but SHOULD NOT be sent as part of the response. If the property is marked as writeOnly being true and is in the required list, the required will take effect on the request only. A property MUST NOT be marked as both readOnly and writeOnly being true. Default value is false.
    :param XML xml: This MAY be used only on properties schemas. It has no effect on root schemas. Adds additional metadata to describe the XML representation of this property.
    :param ExternalDocs external_docs: Additional external documentation for this schema.
    :param Example example: A free-form property to include an example of an instance for this schema. To represent examples that cannot be naturally represented in JSON or YAML, a string value can be used to contain the example with escaping where necessary.
    :param bool deprecated: Specifies that a schema is deprecated and SHOULD be transitioned out of usage. Default value is false.
    """

    def __init__(
            self,
            title=None, multiple_of=None, maximum=None, exclusive_maximum=None, minimum=None, exclusive_minimum=None, max_length=None, min_length=None, pattern=None, max_items=None, min_items=None, unique_items=None, max_properties=None, min_properties=None, required=None, enum=None,
            type_=None, all_of=None, one_of=None, any_of=None, not_=None, items=None, properties=None, additional_properties=None, description=None, format_=None, default=None,
            nullable=None, discriminator=None, read_only=None, write_only=None, xml=None, external_docs=None, example=None, deprecated=None,
    ):
        self.title = title
        self.multiple_of = multiple_of
        self.maximum = maximum
        self.exclusive_maximum = exclusive_maximum
        self.minimum = minimum
        self.exclusive_minimum = exclusive_minimum
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items = unique_items
        self.max_properties = max_properties
        self.min_properties = min_properties
        self.required = required
        self.enum = enum

        self.type_ = type_
        self.all_of = all_of
        self.one_of = one_of
        self.any_of = any_of
        self.not_ = not_
        self.items = items
        self.properties = properties
        self.additional_properties = additional_properties
        self.description = description
        self.format_ = format_
        self.default = default

        self.nullable = nullable
        self.discriminator = discriminator
        self.read_only = read_only
        self.write_only = write_only
        self.xml = xml
        self.external_docs = external_docs
        self.example = example
        self.deprecated = deprecated

    def as_swagger(self):
        doc = {}
        if self.title:
            doc[sw.title] = self.title
        if self.multiple_of:
            doc[sw.multiple_of] = self.multiple_of
        if self.maximum:
            doc[sw.maximum] = self.maximum
        if self.exclusive_maximum:
            doc[sw.exclusive_maximum] = self.exclusive_maximum
        if self.minimum:
            doc[sw.minimum] = self.minimum
        if self.exclusive_minimum:
            doc[sw.exclusive_minimum] = self.exclusive_minimum
        if self.max_length:
            doc[sw.max_length] = self.max_length
        if self.min_length:
            doc[sw.min_length] = self.min_length
        if self.pattern:
            doc[sw.pattern] = self.pattern
        if self.max_items:
            doc[sw.max_items] = self.max_items
        if self.min_items:
            doc[sw.min_items] = self.min_items
        if self.unique_items:
            doc[sw.unique_items] = self.unique_items
        if self.max_properties:
            doc[sw.max_properties] = self.max_properties
        if self.min_properties:
            doc[sw.min_properties] = self.min_properties
        if self.required:
            doc[sw.required] = self.required
        if self.enum:
            doc[sw.enum] = self.enum
        if self.type_:
            doc[sw.type_] = self.type_
        if self.all_of:
            doc[sw.all_of] = self.all_of.as_swagger()
        if self.one_of:
            doc[sw.one_of] = self.one_of.as_swagger()
        if self.any_of:
            doc[sw.any_of] = self.any_of.as_swagger()
        if self.not_:
            doc[sw.not_] = self.not_.as_swagger()
        if self.items:
            doc[sw.items] = self.items.as_swagger()
        if self.properties:
            doc[sw.properties] = self.properties.as_swagger()
        if self.additional_properties:
            doc[sw.additional_properties] = self.additional_properties.as_swagger()
        if self.description:
            doc[sw.description] = self.description
        if self.format_:
            doc[sw.format_] = self.format_
        if self.default:
            doc[sw.default] = self.default
        if self.nullable:
            doc[sw.nullable] = self.nullable
        if self.discriminator:
            doc[sw.discriminator] = self.discriminator.as_swagger()
        if self.read_only:
            doc[sw.read_only] = self.read_only
        if self.write_only:
            doc[sw.write_only] = self.write_only
        if self.xml:
            doc[sw.xml] = self.xml.as_swagger()
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs.as_swagger()
        if self.example:
            doc[sw.example] = self.example.as_swagger()
        if self.deprecated:
            doc[sw.deprecated] = self.deprecated
        return doc


class Parameter(SwaggerObject):
    """Represents a Swagger "Parameter Object"

    :param str name: REQUIRED. The name of the parameter. Parameter names are case sensitive.
If in is "path", the name field MUST correspond to the associated path segment from the path field in the Paths Object. See Path Templating for further information.
If in is "header" and the name field is "Accept", "Content-Type" or "Authorization", the parameter definition SHALL be ignored.
For all other cases, the name corresponds to the parameter name used by the in property.
    :param str in_: REQUIRED. The location of the parameter. Possible values are "query", "header", "path" or "cookie".
    :param str description: A brief description of the parameter. This could contain examples of use. CommonMark syntax MAY be used for rich text representation.
    :param bool required: Determines whether this parameter is mandatory. If the parameter location is "path", this property is REQUIRED and its value MUST be true. Otherwise, the property MAY be included and its default value is false.
    :param bool deprecated: Specifies that a parameter is deprecated and SHOULD be transitioned out of usage. Default value is false.
    :param bool allow_empty_value: Sets the ability to pass empty-valued parameters. This is valid only for query parameters and allows sending a parameter with an empty value. Default value is false. If style is used, and if behavior is n/a (cannot be serialized), the value of allowEmptyValue SHALL be ignored. Use of this property is NOT RECOMMENDED, as it is likely to be removed in a later revision.

    :param str style: Describes how the parameter value will be serialized depending on the type of the parameter value. Default values (based on value of in): for query - form; for path - simple; for header - simple; for cookie - form.
    :param bool explode: When this is true, parameter values of type array or object generate separate parameters for each value of the array or key-value pair of the map. For other types of parameters this property has no effect. When style is form, the default value is true. For all other styles, the default value is false.
    :param bool allow_reserved: Determines whether the parameter value SHOULD allow reserved characters, as defined by RFC3986 :/?#[]@!$&'()*+,;= to be included without percent-encoding. This property only applies to parameters with an in value of query. The default value is false.
    :param Schema or Reference schema: The schema defining the type used for the parameter.
    :param Example example: Example of the media type. The example SHOULD match the specified schema and encoding properties if present. The example field is mutually exclusive of the examples field. Furthermore, if referencing a schema which contains an example, the example value SHALL override the example provided by the schema. To represent examples of media types that cannot naturally be represented in JSON or YAML, a string value can contain the example with escaping where necessary.
    :param dict[str, Example or Reference] examples: Examples of the media type. Each example SHOULD contain a value in the correct format as specified in the parameter encoding. The examples field is mutually exclusive of the example field. Furthermore, if referencing a schema which contains an example, the examples value SHALL override the example provided by the schema.

    :param dict[str, MediaType] content: A map containing the representations for the parameter. The key is the media type and the value describes it. The map MUST only contain one entry.
    """

    def __init__(
            self,
            name, in_,
            description=None, required=None, deprecated=None, allow_empty_value=None,
            style=None, explode=None, allow_reserved=None, schema=None, example=None, examples=None, content=None,
    ):
        self.name = name
        self.in_ = in_
        self.description = description
        self.required = required
        self.deprecated = deprecated
        self.allow_empty_value = allow_empty_value
        self.style = style
        self.explode = explode
        self.allow_reserved = allow_reserved
        self.schema = schema
        self.example = example
        self.examples = examples
        self.content = content

    def as_swagger(self):
        doc = {
            sw.name: self.name,
            sw.in_: self.in_,
        }
        if self.description:
            doc[sw.description] = self.description
        if self.required:
            doc[sw.required] = self.required
        if self.deprecated:
            doc[sw.deprecated] = self.deprecated
        if self.allow_empty_value:
            doc[sw.allow_empty_value] = self.allow_empty_value
        if self.style:
            doc[sw.style] = self.style
        if self.explode:
            doc[sw.explode] = self.explode
        if self.allow_reserved:
            doc[sw.allow_reserved] = self.allow_reserved
        if self.schema:
            doc[sw.schema] = self.schema.as_swagger()
        if self.example:
            doc[sw.example] = self.example.as_swagger()
        if self.examples:
            doc[sw.examples] = {k: v.as_swagger() for k, v in self.examples.items()}
        if self.content:
            doc[sw.content] = {k: v.as_swagger() for k, v in self.content.items()}

        return doc


class PathItem(SwaggerObject):
    """Represents a Swagger "Path Item Object"

    :param str ref: Allows for an external definition of this path item. The referenced structure MUST be in the format of a Path Item Object. If there are conflicts between the referenced definition and this Path Item's definition, the behavior is undefined.
    :param str summary: An optional, string summary, intended to apply to all operations in this path.
    :param str description: An optional, string description, intended to apply to all operations in this path. CommonMark syntax MAY be used for rich text representation.
    :param Operation get: A definition of a GET operation on this path.
    :param Operation put: A definition of a PUT operation on this path.
    :param Operation post: A definition of a POST operation on this path.
    :param Operation delete: A definition of a DELETE operation on this path.
    :param Operation options: A definition of a OPTIONS operation on this path.
    :param Operation head: A definition of a HEAD operation on this path.
    :param Operation patch: A definition of a PATCH operation on this path.
    :param Operation trace: A definition of a TRACE operation on this path.
    :param List[Server] servers: An alternative server array to service all operations in this path.
    :param List[Parameter or Reference] parameters: A list of parameters that are applicable for all the operations described under this path. These parameters can be overridden at the operation level, but cannot be removed there. The list MUST NOT include duplicated parameters. A unique parameter is defined by a combination of a name and location. The list can use the Reference Object to link to parameters that are defined at the OpenAPI Object's components/parameters.
    """

    def __init__(
            self,
            ref=None, summary=None, description=None,
            get=None, put=None, post=None, delete=None, options=None, head=None, patch=None, trace=None,
            servers=None, parameters=None,
    ):
        self.ref = ref
        self.summary = summary
        self.description = description
        self.get = get
        self.put = put
        self.post = post
        self.delete = delete
        self.options = options
        self.head = head
        self.patch = patch
        self.trace = trace
        self.servers = servers
        self.parameters = parameters

    def as_swagger(self):
        doc = {}
        if self.ref:
            doc[sw.ref] = self.ref
        if self.summary:
            doc[sw.summary] = self.summary
        if self.description:
            doc[sw.description] = self.description
        if self.get:
            doc[sw.get] = self.get.as_swagger()
        if self.put:
            doc[sw.put] = self.put.as_swagger()
        if self.post:
            doc[sw.post] = self.post.as_swagger()
        if self.delete:
            doc[sw.delete] = self.delete.as_swagger()
        if self.options:
            doc[sw.options] = self.options.as_swagger()
        if self.head:
            doc[sw.head] = self.head.as_swagger()
        if self.patch:
            doc[sw.patch] = self.patch.as_swagger()
        if self.trace:
            doc[sw.trace] = self.trace.as_swagger()
        if self.servers:
            doc[sw.servers] = [i.as_swagger() for i in self.servers]
        if self.parameters:
            doc[sw.parameters] = [i.as_swagger() for i in self.parameters]
        return doc
#
#
# class Paths(SwaggerObject):
#     """Represents a Swagger "Paths Object"
#
#     :param dict[str, PathItem] paths: A relative path to an individual endpoint. The field name MUST begin with a slash. The path is appended (no relative URL resolution) to the expanded URL from the Server Object's url field in order to construct the full URL. Path templating is allowed. When matching URLs, concrete (non-templated) paths would be matched before their templated counterparts. Templated paths with the same hierarchy but different templated names MUST NOT exist as they are identical. In case of ambiguous matching, it's up to the tooling to decide which one to use.
#     """
#
#     def __init__(self, paths=None):
#         self.paths = paths
#
#     def add(self, path_key, path_item):
#         self.paths[path_key] = path_item
#
#     def get(self, path_key):
#         return self.paths[path_key]
#
#     def has_key(self, path_key):
#         return path_key in self.paths
#
#     def as_swagger(self):
#         doc = {
#             sw.paths: {
#                 path_key: path_item.as_swagger()
#                 for path_key, path_item in self.paths.items()
#             },
#         }
#         return doc


class Components(SwaggerObject):
    """Represents a Swagger "Components Object"

    :param dict(str, Schema or Reference) schemas: An object to hold reusable Schema Objects.
    :param dict(str, Response or Reference) responses: An object to hold reusable Response Objects.
    :param dict(str, Parameter or Reference) parameters: An object to hold reusable Parameter Objects.
    :param dict(str, Example or Reference) examples: An object to hold reusable Example Objects.
    :param dict(str, RequestBody or Reference) request_bodies: An object to hold reusable Request Body Objects.
    :param dict(str, Header or Reference) headers: An object to hold reusable Header Objects.
    :param dict(str, SecurityScheme or Reference) security_schemes: An object to hold reusable Security Scheme Objects.
    :param dict(str, Link or Reference) links: An object to hold reusable Link Objects.
    :param dict(str, Callback or Reference) callbacks: An object to hold reusable Callback Objects.
    """

    def __init__(
            self,
            schemas=None, responses=None, parameters=None, examples=None, request_bodies=None, headers=None,
            security_schemes=None, links=None, callbacks=None
    ):
        self.schemas = schemas
        self.responses = responses
        self.parameters = parameters
        self.examples = examples
        self.request_bodies = request_bodies
        self.headers = headers
        self.security_schemes = security_schemes
        self.links = links
        self.callbacks = callbacks

    def as_swagger(self):
        doc = {}
        if self.schemas:
            doc[sw.schemas] = {k: v.as_swagger() for k, v in self.schemas.items()}
        if self.responses:
            doc[sw.responses] = {k: v.as_swagger() for k, v in self.responses.items()}
        if self.parameters:
            doc[sw.parameters] = {k: v.as_swagger() for k, v in self.parameters.items()}
        if self.examples:
            doc[sw.examples] = {k: v.as_swagger() for k, v in self.examples.items()}
        if self.request_bodies:
            doc[sw.request_bodies] = {k: v.as_swagger() for k, v in self.request_bodies.items()}
        if self.headers:
            doc[sw.headers] = {k: v.as_swagger() for k, v in self.headers.items()}
        if self.security_schemes:
            doc[sw.security_schemes] = {k: v.as_swagger() for k, v in self.security_schemes.items()}
        if self.links:
            doc[sw.links] = {k: v.as_swagger() for k, v in self.links.items()}
        if self.callbacks:
            doc[sw.callbacks] = {k: v.as_swagger() for k, v in self.callbacks.items()}
        return {}


class SecurityRequirement(SwaggerObject):
    """Represents a Swagger "Security Requirement Object"

    :param str name: The name used for each property MUST correspond to a security scheme declared in the Security Schemes under the Components Object.
    :param list[str] values: Each name MUST correspond to a security scheme which is declared in the Security Schemes under the Components Object. If the security scheme is of type "oauth2" or "openIdConnect", then the value is a list of scope names required for the execution. For other security scheme types, the array MUST be empty.
    """

    def __init__(self, name, values):
        self.name = name
        self.values = values

    def as_swagger(self):
        doc = {self.name: self.values}
        return doc


class OpenAPI(SwaggerObject):
    """Represents a Swagger "OpenAPI Object"

    :param str openapi: REQUIRED. This string MUST be the semantic version number of the OpenAPI Specification version that the OpenAPI document uses. The openapi field SHOULD be used by tooling specifications and clients to interpret the OpenAPI document. This is not related to the API info.version string.
    :param Info info: REQUIRED. Provides metadata about the API. The metadata MAY be used by tooling as required.
    :param list[Server] servers: An array of Server Objects, which provide connectivity information to a target server. If the servers property is not provided, or is an empty array, the default value would be a Server Object with a url value of /.
    :param dict[str, PathItem] paths: REQUIRED. The available paths and operations for the API.
    :param Components components: An element to hold various schemas for the specification.
    :param list[SecurityRequirement] security: A declaration of which security mechanisms can be used across the API. The list of values includes alternative security requirement objects that can be used. Only one of the security requirement objects need to be satisfied to authorize a request. Individual operations can override this definition.
    :param List[Tag] tags: A list of tags used by the specification with additional metadata. The order of the tags can be used to reflect on their order by the parsing tools. Not all tags that are used by the Operation Object must be declared. The tags that are not declared MAY be organized randomly or based on the tools' logic. Each tag name in the list MUST be unique.
    :param ExternalDocumentation external_docs: Additional external documentation.
    """
    def __init__(
            self,
            openapi, info, paths,
            servers=None, components=None, security=None, tags=None, external_docs=None
    ):
        self.openapi = openapi
        self.info = info
        self.servers = servers
        self.paths = paths
        self.components = components
        self.security = security
        self.tags = tags
        self.external_docs = external_docs

    def as_swagger(self):
        doc = {
            sw.openapi: self.openapi,
            sw.info: self.info.as_swagger(),
            sw.paths: {
                path_key: path_item.as_swagger()
                for path_key, path_item in self.paths.items()
            },
        }
        if self.servers:
            doc[sw.servers] = [i.as_swagger() for i in self.servers]
        if self.components:
            doc[sw.components] = self.components.as_swagger()
        if self.security:
            doc[sw.security] = [i.as_swagger() for i in self.security]
        if self.tags:
            doc[sw.tags] = [i.as_swagger() for i in self.tags]
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs.as_swagger()
        return doc
