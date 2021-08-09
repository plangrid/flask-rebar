Version History
---------------

This Version History provides a high-level overview of changes in major versions. It is intended as a supplement
for :doc:`changelog`. In this document we highlight major changes, especially breaking changes. If you notice a breaking
change that we neglected to note here, please let us know (or open a PR to add it to this doc)!

Version 2.0 (2021-07-26)
========================

Errata
******
Version 2.0.0 included a couple of bugs related to the upgrade from Marshmallow 2 to 3. While the fix for one of those
(removal of ``DisallowExtraFieldsMixin``) might technically be considered a "breaking change" requiring a new major
version, we deemed it acceptable to bend the rules of semantic versioning since that mixin **never actually functioned**
in 2.0.0.

*  Removed support for versions < 3.6 of Python
*  Removed support for versions < 1.0 of Flask, and added support for Flask 2.x; we now support only Flask 1.x and 2.x.
*  Removed support for versions < 3.0 of Marshmallow; we now support only Marshmallow 3.x
*  (2.0.1) Removed ``flask_rebar.validation.DisallowExtraFieldsMixin`` - with Marshmallow 3, this is now default behavior and this mixin was broken in 2.0.0
  * We now generate appropriate OpenAPI spec based on ``Schema``'s ``Meta`` (ref https://marshmallow.readthedocs.io/en/stable/quickstart.html#handling-unknown-fields)
*  Removed support for previously deprecated parameter names (https://github.com/plangrid/flask-rebar/pull/246/files)
  * In methods that register handlers, ``marshal_schema`` is now ``response_body_schema`` and the former name is no longer supported
  * ``AuthenticatorConverterRegistry`` no longer accepts a ``converters`` parameter when instantiating. Use ``register_type`` on an instance to add a converter
*  Standardized registration of custom swagger authenticator converters (https://github.com/plangrid/flask-rebar/pull/216)
  * Use of "converter functions" is no longer supported; use a class that derives from ``AuthenticatorConverter`` instead.
*  Added "rebar-internal" error codes (https://github.com/plangrid/flask-rebar/pull/245)
  * Can be used programmatically to differentiate between different "flavors" of errors (for example, the specific reason behind a ``400 Bad Request``)
  * This gets added to the JSON we return for errors
*  Added support for marshmallow-objects >= 2.3, < 3.0 (https://github.com/plangrid/flask-rebar/pull/243)
  * You can now use a marshmallow-objects ``Model`` instead of a marshmallow ``Schema`` when registering your endpoints.
*  Add support for "hidden API" endpoints that are by default not exposed in generated OpenAPI spec (https://github.com/plangrid/flask-rebar/pull/191/files)


Version 1.0 (2018-03-04)
========================
The first official release of Flask-Rebar!

