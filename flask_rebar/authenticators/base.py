"""
    Base Authenticator
    ~~~~~~~~~~~~~~~~~~

    Base class for authenticators.

    :copyright: Copyright 2018 PlanGrid, Inc., see AUTHORS.
    :license: MIT, see LICENSE for details.
"""


class Authenticator(object):
    """
    Abstract authenticator class. Custom authentication methods should
    extend this class.
    """

    def authenticate(self):
        """
        Implementations of :class:`Authenticator` should override this method.

        This will be called before a request handler is called, and should raise
        an :class:`flask_rebar.errors.HttpJsonError` is authentication fails.

        Otherwise the return value is ignored.

        :raises: :class:`flask_rebar.errors.Unauthorized`
        """
        raise NotImplemented
