from abc import ABCMeta
from abc import abstractmethod

from flask_rebar.swagger_generation import swagger_words as sw


class SwaggerObject:
    @abstractmethod
    def as_swagger(self):
        """
        Create a Swagger representation of this object

        :rtype: dict
        """
        raise NotImplementedError()


class Reference(SwaggerObject):
    """
    Represents a Swagger "Reference Object"

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


class Server(SwaggerObject):
    """Represents a Swagger "Server Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        return {}


class Operation(SwaggerObject):
    """Represents a Swagger "Operation Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        return {}


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
    :param List[Parameter|Reference] parameters: A list of parameters that are applicable for all the operations described under this path. These parameters can be overridden at the operation level, but cannot be removed there. The list MUST NOT include duplicated parameters. A unique parameter is defined by a combination of a name and location. The list can use the Reference Object to link to parameters that are defined at the OpenAPI Object's components/parameters.
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


class Paths(SwaggerObject):
    """Represents a Swagger "Paths Object"

    :param dict[str, PathItem] paths: A relative path to an individual endpoint. The field name MUST begin with a slash. The path is appended (no relative URL resolution) to the expanded URL from the Server Object's url field in order to construct the full URL. Path templating is allowed. When matching URLs, concrete (non-templated) paths would be matched before their templated counterparts. Templated paths with the same hierarchy but different templated names MUST NOT exist as they are identical. In case of ambiguous matching, it's up to the tooling to decide which one to use.
    """

    def __init__(self, paths):
        self.paths = paths

    def as_swagger(self):
        doc = {
            sw.paths: {
                path_key: path_item.as_swagger()
                for path_key, path_item in self.paths.items()
            },
        }
        return doc


class Components(SwaggerObject):
    """Represents a Swagger "Components Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        return {}


class SecurityRequirement(SwaggerObject):
    """Represents a Swagger "Security Requirement Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        return {}


class OpenAPI(SwaggerObject):
    """Represents a Swagger "OpenAPI Object"

    :param str openapi: REQUIRED. This string MUST be the semantic version number of the OpenAPI Specification version that the OpenAPI document uses. The openapi field SHOULD be used by tooling specifications and clients to interpret the OpenAPI document. This is not related to the API info.version string.
    :param Info info: REQUIRED. Provides metadata about the API. The metadata MAY be used by tooling as required.
    :param List[Server] servers: An array of Server Objects, which provide connectivity information to a target server. If the servers property is not provided, or is an empty array, the default value would be a Server Object with a url value of /.
    :param Paths paths: REQUIRED. The available paths and operations for the API.
    :param Components components: An element to hold various schemas for the specification.
    :param List[SecurityRequirement] security: A declaration of which security mechanisms can be used across the API. The list of values includes alternative security requirement objects that can be used. Only one of the security requirement objects need to be satisfied to authorize a request. Individual operations can override this definition.
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
            sw.paths: self.paths.as_swagger(),
        }
        if self.servers:
            doc[sw.servers] = self.servers
        if self.components:
            doc[sw.components] = self.components
        if self.security:
            doc[sw.security] = self.security
        if self.tags:
            doc[sw.tags] = [i.as_swagger() for i in self.tags]
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs.as_swagger()
        return doc
