from flask import g
from werkzeug.local import LocalProxy

# Werkzeug LocalProxy that can be used to retrieved the toolbox attached to
# the current application context.
toolbox_proxy = LocalProxy(lambda: g.toolbox)