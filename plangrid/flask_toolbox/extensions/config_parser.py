from __future__ import unicode_literals

from collections import namedtuple

_ConfigParserParam = namedtuple(
    '_ConfigParserParam',
    ['name', 'coerce', 'default', 'required']
)


class MissingConfiguration(Exception):
    pass


class ConfigParser(object):
    def __init__(self):
        self.params = []

    def add_param(
            self,
            name,
            coerce=None,
            default=None,
            required=False,
    ):
        self.params.append(
            _ConfigParserParam(
                name=name,
                coerce=coerce,
                default=default,
                required=required
            )
        )

    def resolve(self, sources):
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
