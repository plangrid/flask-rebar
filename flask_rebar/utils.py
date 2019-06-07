"""
    General-Purpose Utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities that are not specific to request-handling (you'll find those in request_utils.py).

    :copyright: Copyright 2019 Autodesk, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

import functools
import warnings


def deprecated_parameters(warn_type=FutureWarning, **aliases):
    """
    Adapted from https://stackoverflow.com/a/49802489/977046
    :param Warning warn_type: Use (ignored by default) DeprecationWarning for quieter operation
    :param aliases: Keyword args in the form {old_param_name = Union[new_param_name, (new_param_name, eol_version)]}
                    where eol_version is the version in which the alias may case to be recognized
    :return: function decorator that will apply aliases to param names and raise DeprecationWarning
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            _rename_kwargs(f.__name__, kwargs, aliases, warn_type)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def _rename_kwargs(func_name, kwargs, aliases, warn_type):
    """
    Adapted from https://stackoverflow.com/a/49802489/977046
    """
    for alias, new_spec in aliases.items():
        if alias in kwargs:
            if type(new_spec) is tuple:
                new = str(new_spec[0])
                eol_version = str(new_spec[1])
            else:
                new = str(new_spec)
                eol_version = None
            if new in kwargs:
                raise TypeError(
                    "{} received both {} and {}".format(func_name, alias, new)
                )
            eol_clause = (
                " and may be removed in version {}".format(eol_version)
                if eol_version
                else ""
            )
            msg = "{} is deprecated{}; use {}".format(alias, eol_clause, new)
            warnings.warn(msg, warn_type)
            kwargs[new] = kwargs.pop(alias)
