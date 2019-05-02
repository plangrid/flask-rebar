"""
    Swagger Objects
    ~~~~~~~~~~~~~~~

    Python representations of select Swagger Objects.

    These are objects that aren't extractable from Flask or the Flask-Rebar handler registries
    and need to be manually set.

    :copyright: Copyright 2019 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""
from flask_rebar.swagger_generation import swagger_words as sw


class ExternalDocumentation(object):
    """Represents a Swagger "External Documentation Object"

    :param str url: The URL for the target documentation. Value MUST be in the format of a URL
    :param str description: A short description of the target documentation
    """

    def __init__(self, url, description=None):
        self.url = url
        self.description = description

    def as_swagger(self):
        """Create a Swagger representation of this object

        :rtype: dict
        """
        doc = {sw.url: self.url}
        if self.description:
            doc[sw.description] = self.description
        return doc


class Tag(object):
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
        """Create a Swagger representation of this object

        :rtype: dict
        """
        doc = {sw.name: self.name}
        if self.description:
            doc[sw.description] = self.description
        if self.external_docs:
            doc[sw.external_docs] = self.external_docs.as_swagger()
        return doc


class ServerVariable(object):
    """Represents a Swagger "Server Variable Object"

    :param str default:
    :param str description:
    :param list[str] enum:
    """

    def __init__(self, default, description=None, enum=None):
        self.default = default
        self.description = description
        self.enum = enum

    def as_swagger(self):
        """Create a Swagger representation of this object

        :rtype: dict
        """
        doc = {sw.default: self.default}
        if self.description:
            doc[sw.description] = self.description
        if self.enum:
            doc[sw.enum] = self.enum
        return doc


class Server(object):
    """Represents a Swagger "Server Object"

    :param str url:
    :param str description:
    :param dict[str, ServerVariable] variables:
    """

    def __init__(self, url, description=None, variables=None):
        self.url = url
        self.description = description
        self.variables = variables

    def as_swagger(self):
        """Create a Swagger representation of this object

        :rtype: dict
        """
        doc = {sw.url: self.url}
        if self.description:
            doc[sw.description] = self.description
        if self.variables:
            doc[sw.variables] = {k: v.as_swagger() for k, v in self.variables.items()}
        return doc
