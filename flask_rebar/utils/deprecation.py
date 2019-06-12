"""
    General-Purpose Utilities
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Utilities that are not specific to request-handling (you'll find those in request_utils.py).

    :copyright: Copyright 2019 Autodesk, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""

import copy
import functools
import warnings

from werkzeug.local import LocalProxy as module_property  # noqa


# ref http://jtushman.github.io/blog/2014/05/02/module-properties/ for background on
# use of werkzeug LocalProxy to simulate "module properties"
# end result: singleton config can be accessed by, e.g.,
#    from flask_rebar.utils.deprecation import config as deprecation_config
#    deprecation_config.warning_type = YourFavoriteWarning


class DeprecationConfig:
    """
    Singleton class to allow one-time set of deprecation config controls
    """

    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if DeprecationConfig.__instance is None:
            DeprecationConfig()
        return DeprecationConfig.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if DeprecationConfig.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            DeprecationConfig.__instance = self
            self.warning_type = FutureWarning


@module_property
def config():
    return DeprecationConfig.getInstance()


def deprecated(new_func=None, eol_version=None):
    """
    :param Union[str, (str, str)] new_func: Name (or name and end-of-life version) of replacement
    :param str eol_version: Version in which this function may no longer work
    :return:
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            new = None
            eol = eol_version
            if (
                type(new_func) is tuple
            ):  # in case somebody inferred this from the way we deprecate params..
                new = str(new_func[0])
                eol = str(new_func[1])
            elif new_func:
                new = str(new_func)
            _deprecation_warning(f.__name__, new, eol)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def deprecated_parameters(**aliases):
    """
    Adapted from https://stackoverflow.com/a/49802489/977046
    :param aliases: Keyword args in the form {old_param_name = Union[new_param_name, (new_param_name, eol_version)]}
                    where eol_version is the version in which the alias may case to be recognized
    :return: function decorator that will apply aliases to param names and raise DeprecationWarning
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            new_kwargs = _remap_kwargs(f.__name__, kwargs, aliases)
            return f(*args, **new_kwargs)

        return wrapper

    return decorator


def _remap_kwargs(func_name, kwargs, aliases):
    """
    Adapted from https://stackoverflow.com/a/49802489/977046
    """
    remapped_args = copy.deepcopy(kwargs)
    for alias, new_spec in aliases.items():
        if alias in remapped_args:
            eol_version = None
            if type(new_spec) is tuple:
                new = str(new_spec[0])
                if len(new_spec) >= 2:
                    eol_version = str(new_spec[1]) if new_spec[1] else None
            else:
                new = str(new_spec)
            if new in remapped_args:
                raise TypeError(
                    "{} received both {} and {}".format(func_name, alias, new)
                )
            else:
                _deprecation_warning(alias, new, eol_version)
                remapped_args[new] = remapped_args.pop(alias)

    return remapped_args


def _deprecation_warning(old_name, new_name, eol_version):
    eol_clause = (
        " and may be removed in version {}".format(eol_version) if eol_version else ""
    )
    replacement_clause = "; use {}".format(new_name) if new_name else ""
    msg = "{} is deprecated{}{}".format(old_name, eol_clause, replacement_clause)
    warnings.warn(msg, config.warning_type)
