from __future__ import unicode_literals

from collections import namedtuple

_ConfigParserParam = namedtuple(
    '_ConfigParserParam',
    ['name', 'coerce', 'default', 'required']
)


class MissingConfiguration(Exception):
    pass


def truthy(val):
    """
    Coerces a value that might've come from an environment variable to a boolean.

    It works like this::

        for val in (True, 'True', 'true', '1', 1):
            assert truthy(val) is True

        for val in (False, 'False', 'false', '0', 0, None):
            assert truthy(val) is False
    """
    return str(val).lower() in ('true', '1')


class ConfigParser(object):
    """Resolves configuration parameters for extensions"""

    def __init__(self):
        self.params = []

    def add_param(
            self,
            name,
            coerce=None,
            default=None,
            required=False,
    ):
        """
        Adds parameter for the parser.

        :param str name:
            The name of the parameter. This will be the name the parser looks
            for in sources
        :param Callable coerce:
            If this is included, call this function on the resulting value
            after finding it in a source
        :param default:
            Default value to use for this parameter if it is not found in any
            source
        :param bool required:
            If True, throw an error if this parameter is not found in any source
        """
        self.params.append(
            _ConfigParserParam(
                name=name,
                coerce=coerce,
                default=default,
                required=required
            )
        )

    def resolve(self, sources):
        """
        Resolves the parameters from the provided sources, in order.

        This will look look through each source in order until a parameter
        is found. This is super handy when there is a long chain of fallback
        sources
        (e.g. extension object -> application config -> environment variables)

        :param list[dict]|tuple[dict] sources:
        :rtype: dict
        :returns: dictionary including all the added parameters
        """
        resolved = {}

        for param in self.params:
            for source in sources:
                if param.name in source:
                    val = source[param.name]

                    if param.coerce:
                        val = param.coerce(val)

                    resolved[param.name] = val

                    break

            else:
                if param.required and not param.default:
                    raise MissingConfiguration(param.name)
                else:
                    resolved[param.name] = param.default

        return resolved
