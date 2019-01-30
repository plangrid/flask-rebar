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


class PathItem(SwaggerObject):
    """Represents a Swagger "Path Item Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        return {}


class Paths(SwaggerObject):
    """Represents a Swagger "Paths Object"

    :param TODO
    """

    def __init__(self):
        pass

    def as_swagger(self):
        return {}


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
            doc[sw.tags] = self.tags
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs
        return doc
