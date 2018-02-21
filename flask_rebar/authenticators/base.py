class USE_DEFAULT(object):
    pass


class Authenticator(object):
    """
    Abstract authenticator class. Custom authentication methods should
    extend this class.
    """
    def authenticate(self):
        raise NotImplemented
