Changelog
=========


v1.12.0 (2020-01-08)
--------------------

Changes
~~~~~~~
- Added support for marshmallow partial schema (#146) [Tuan Anh Hoang-
  Vu]

- Pin to PyYAML to avoid breaking change (Python 3.4) until we release our 2.0 and cut those old cords [Rick Riensche]

Other
~~~~~
- Doc: Added tutorial section for linking blogs and other external
  resources. (#143) [Andrew Standley]


v1.11.0 (2019-10-28)
--------------------
- Improve swagger support for authenticators (#130) (BP-778. [Andrew
  Standley]

  * Added a get_open_api_version method to the swagger generator interface to help with refactoring the swagger tests so that we can use generators that have customer converters registered.

  * Updated jsonschema library for tests.

  * Added failing tests for swagger generation from Authenticators.

  * Added tests for the interface of AuthenticatorConverter to make sure I don't accidentally change it.

  * Added authenticator to swagger conversion framework.

  * Updated the multiple_authenticators test to use the new auth converter framework.

  * Fixed eol_version for a deprecation message, and caught warnings on the legacy AuthenticatorConverter test.

  * Fix typos and imports.

  * Added documentation to AuthenticatorConverter. Also noted potential issue with conflicting scheme names in generators, going to push addressing that to later.

  * Added combined authentication examples to the recipes doc.


v1.10.2 (2019-09-19)
--------------------

Fix
~~~
- Update authenticators to catch Forbidden exception (#133) [Marc-Éric]


v1.10.1 (2019-09-19)
--------------------

Changes
~~~~~~~
- Tweaking build rules, updating docs, and prepping for bumpversion do-
  over. [Rick Riensche]

Fix
~~~
- Treat "description" key the same way as "explode" key for query and h…
  (#129) [Artem Revenko]

Other
~~~~~
- Accept bare class for schema arguments (#126) [Rick Riensche]
- Fix marshmallow test helpers so that they work will all unittest
  compatible frameworks and not just pytest. 'python setup.py test'
  works again. (#127) [Andrew Standley]


v1.10.0 (2019-09-11)
--------------------
- BP-763: Add support for multiple authenticators (#122) [Andrew
  Standley]

  * Added the ability to specify a conversion function for deprecated params.

  * Added support for defining authentication with a list of Authenticators; None, a single Authenticator, and USE_DEFAULT(where applicable) are still valid values. The authenticator parameter becomes authenticators; authenticator is still usable until 3.0 via the deprecation wrappers. The default_authenticator parameter becomes default_authenticators; default_authenticator is still usable until 3.0 via the deprecation wrappers. This change affects PathDefinition, HandlerRegistry, Rebar, SwaggerGeneratorI, SwaggerV2Generator, and SwaggerV3Generator. Note: It's an open question how best to handle returning the errors when all authenticators fail. For now we are returning the first error with the assumption that the first authenticator is the 'preferred' one; this also preserves the previous behaviour.

  * Updated docs.
- [FEATURE] adding too many requests error (#120) [Fabian]


v1.9.1 (2019-08-20)
-------------------

Fix
~~~
- 118 - pinned to an incompatible version of Marshmallow (3.0.0) [Rick Riensche]

  * Changes between 3.0.0rc5 and the actual release of 3.0.0 made our presumptive compatibility changes no longer sufficient

- Relax overly-sensitive test (#117) [Rick Riensche]

  * Deals with a subtle change in returned data on "Invalid input type" schema validation error between marshmallow 2.19 and 2.20. In return from Schema.load, "data" changed from empty dictionary to None, and we had an overzealous test that was expecting empty dictionary; whereas the value of "data" in this scenario appears to be undefined.


v1.9.0 (2019-07-24)
-------------------

New
~~~
- Graceful deprecation rename of marshal_schema to response_body_schema
  (#101) [Rick Riensche]

  * chg: Refactor utilities into a separate utils package

Changes
~~~~~~~
- Move USE_DEFAULT to utils (#107) [retornam]
- Use extras_require for dev requirements (#106) [retornam]
- Allow /swagger/ui to resolve to swagger UI without redirect (#102)
  [Michael Bryant]

Fix
~~~
- Revert the red-herring sphinx conf change, add readthedocs yaml
  config. [Rick Riensche]
- Broke sphinx when we removed requirements.txt (#111) [Rick Riensche]

Other
~~~~~
- Run exception handlers on sys exit. [Brock Haywood]
- Doc: add code of conduct, based on https://www.contributor-
  covenant.org/ (#108) [Fabian]
- Fix(pypi): update pypi password (#105) [Sonny Van]
- Updated changelog. [Brock Haywood]


v1.8.1 (2019-06-14)
-------------------

Changes
~~~~~~~
- Deprecation util cleaned up and expanded a bit. More forgiving of unexpected inputs. [Rick Riensche]

Fix
~~~
- Bug in v1.8.0 deprecation util - deepcopy inadvertently replacing things like default_authenticator


v1.8.0 (2019-06-12)
-------------------

New
~~~
- Graceful deprecation rename of marshal_schema to response_body_schema
  (#101) [Rick Riensche]

- Refactor utilities into a separate utils package including new deprecation utility

Changes
~~~~~~~
- Allow /swagger/ui to resolve to swagger UI without redirect (#102)
  [Michael Bryant]


v1.7.0 (2019-06-05)
-------------------
- Fixes a bug where http 400s are returned as http 500s (#99) [Brock
  Haywood]

  this is for a case where a werkzeug badrequest exception is raised
  before the rebar handlers get invoked. this was causing the
  default rebar exception handler to run, thus returning a 500
- Updating Contributing page to reflect revised issue review process
  (#95) [Rick Riensche]
- Fix #96 - Flask no longer treats redirects as errors (#97) [Rick
  Riensche]


v1.6.3 (2019-05-10)
-------------------
- Respect user-provided content type in all cases. [Joe Bryan]
- Add default_mimetype to registry. [Joe Bryan]
- Return empty object not empty string, if an empty non-null object
  response is specified. [Joe Bryan]


v1.6.2 (2019-05-08)
-------------------

Fix
~~~
- DELETE requests should return specified Content-Type (#85) [Joe Bryan]


v1.6.1 (2019-05-03)
-------------------

Fix
~~~
- Quick rehacktor to unbreak import statements like "from flask_rebar.swagger_generation.swagger_generator import SwaggerV2Generator"
  (#86) [Rick Riensche]


v1.6.0 (2019-05-02)
-------------------
- Add OpenAPI 3 Support (#80) [barak]
- Sort required array (#81) [Brandon Weng]
- Doc: List Flask-Rebar-Auth0 as an extension (#76) [barak]
- Minor changelog manual cleanup. [Rick Riensche]
- Doc: update changelog. [Rick Riensche]


v1.5.1 (2019-03-22)
-------------------

Fix
~~~
- Werkzeug 0.14->0.15 introduced some breaking changes in redirects
  (#73) [Rick Riensche]

v1.5.0 (2019-03-22)
-------------------

Changes
~~~~~~~
- Enforce black on PR's (#68) [Julius Alexander IV, Fabian]
- Updated todo example to show tag usage (#59) [Fabian]

Fix
~~~
- Do not rethrow redirect errors (#65) [Julius Alexander IV]

Other
~~~~~
- Doc: one more minor tweak to our "SLA" (#71) [Rick Riensche]
- Doc: minor doc cleanup, addition of "SLA-esque" statement to
  Contributing (#70) [Rick Riensche]
- Fix minor formatting issue in docs. [Rick Riensche]
- Add recipe for class based views (#63) [barak]
- Adds a codeowners file (#66) [Brock Haywood]
- Update changelog. [Julius Alexander]


v1.4.1 (2019-02-19)
-------------------

Fix
~~~
- Change schemes=() default so Swagger UI infers scheme from document
  URL (#61) [twosigmajab]

Other
~~~~~
- Update changelog. [Julius Alexander]


v1.4.0 (2019-01-31)
-------------------

New
~~~
- Add gitchangelog (#56) [Julius Alexander IV]

Other
~~~~~
- Support for tags (#55) [barak]
- Add 'https' to default schemes (#53) [twosigmajab]


v1.3.0 (2018-12-04)
-------------------
- Prepare for Marshmallow version 3 (#43) [barak]


v1.2.0 (2018-11-29)
-------------------
- Dump_only=True -> readOnly (#42) [twosigmajab]

  Fixes #39.
- Fix "passowrd" typo in swagger_words (#40) [twosigmajab]
- Rm superfluous logic in swagger_ui.blueprint.show (#38) [twosigmajab]
- Respect many=True in swagger_generator. (#45) [twosigmajab]

  Fixes #41.


v1.1.0 (2018-11-13)
-------------------
- Allow disabling OrderedDicts in generated swagger (#32) [twosigmajab]
- Improve marshal_schema and response header handling (#28) [barak]
- Update release docs. (#31) [Julius Alexander IV]
- Merge pull request #34 from plangrid/required-field-enforce-
  validation. [Joe Bryan]

  Enforce field validators when using ActuallyRequireOnDumpMixin
- Merge branch 'master' into required-field-enforce-validation. [Joe
  Bryan]
- Merge pull request #35 from plangrid/sort-query-params. [Joe Bryan]

  Sort query params for consistent output
- Sort query params for consistent output. [Joe Bryan]
- Use marshmallow built in validation. [Joe Bryan]
- Enforce field validators when using ActuallyRequireOnDumpMixin. [Joe
  Bryan]


v1.0.8 (2018-10-30)
-------------------
- Use built in library for version comparison (#29) [barak]


v1.0.7 (2018-10-29)
-------------------
- Handle RequestRedirect errors properly (#25) [barak]
- Fix docs about specifying custom swagger generator (#23) [barak]


v1.0.6 (2018-10-11)
-------------------
- Changed default 'produces' of swagger generation to 'application/json'
  (#19) [barak]


v1.0.4 (2018-04-05)
-------------------
- Feat(type): added path. [Anthony Martinet]


v1.0.3 (2018-03-27)
-------------------
- Re-raise uncaught errors in debug mode (#14) [barak]
- Add Swagger UI data files to MANIFEST.in. [barakalon]


v1.0.2 (2018-03-07)
-------------------
- Get Travis to deploy again. [barakalon]


v1.0.1 (2018-03-07)
-------------------
- Use find_packages in setup.py. [barakalon]
- Fix README example. [barakalon]
- Break pypi release into its own job. [barakalon]
- Prevent double travis builds for PRs. [barakalon]
- Clarify PyPI release instructions. [barakalon]


v1.0.0 (2018-03-04)
-------------------
- Rename marshal_schemas to marshal_schema. [barakalon]
- Add badge and some documentation for releasing. [barakalon]


v0.1.0 (2018-03-03)
-------------------
- Add deployment to PyPI. [barakalon]
- Remove client_test since its not working for python2.7 and needs more
  testing/documentation. [barakalon]
- Adding travis yaml file. [barakalon]
- Move why flask-rebar documetnation to sphinx only. [barakalon]
- Adding ReadTheDocs. [barakalon]
- Add lots of documentation. [barakalon]
- Split registry out and add prefixing. [barakalon]
- Remove flask_swagger_ui dependency. [barakalon]
- Example app and pytest. [barakalon]
- Refactoring to a smaller package. [barakalon]
- Moving tests directories around. [barakalon]
- Move authenticators to package root. [barakalon]
- Rename framing to swagger_generation. [barakalon]
- Move registry to package root. [barakalon]
- Rename extension to registry. [barakalon]
- Packaging boilerplate. [barakalon]
- Some packaging updates. [barakalon]
- Flask_toolbox -> flask_rebar. [barakalon]
- Get rid of plangrid namespace. [barakalon]
- Cleanup some files. [barakalon]
- Sort generated swagger alphabetically (#46) [colinhostetter]
- Don't ship tests or examples in installed package. [Tom Lippman]
- Add framer env variables to readme. [barakalon]
- Support configuring Framer auth without app. [Nathan Yergler]
- Fixes UUID and ObjectId fields: - honor the allow_none keyword - but
  don't pass validation for an empty string. [Tom Lippman]

  Also adds a function to dynamically subclass any Field or Schema to
  add checking validation logic on serialization.
- Update bugsnag to 3.4.0. [Nathan Yergler]
- Add PaginatedListOf and SkipLimitSchema helpers (#41) [colinhostetter]
- Add configuration for bumpversion utility. [Nathan Yergler]
- Add utility for testing with swagger generated client libraries.
  [Nathan Yergler]
- Fix converter handling in swagger generator. [colinhostetter]
- Bump version to 2.3.0. [barakalon]
- Allow for paginated data. [barakalon]
- Bump version to 2.2.0. [barakalon]
- Add default headers to bootstrapping. [barakalon]
- Fix up the README a little bit. [barakalon]
- Bump version to 2.1.1. [barakalon]
- Fix up some of the package interface. [barakalon]
- Bump major version. [barakalon]
- Some more marshmallow to jsonschema fields. [barakalon]
- Default headers. [barakalon]
- Example app. [barakalon]
- Refactor tests a bit. [barakalon]
- CACA-468 Fix DisallowExtraFields erroring for bad input. [Julius
  Alexander]
- Bump version 1.7.1. [barak-plangrid]
- Gracefully handle missing marshmallow validators in swagger generator.
  [barak-plangrid]
- Publicize marshmallow formatting. [barak-plangrid]
- Move swagger ui to flask toolbox. [barak-plangrid]
- Add back some commits lost in rebase. [barak-plangrid]
- Explicitly import bugsnag.flask. [Nathan Yergler]
- Allow apps to pass in their swagger generator. [Nathan Yergler]
- Allow specification of API description. [Nathan Yergler]
- Swagger endpoint. [barak-plangrid]
- Add check the the swagger we're producing is valid. [barak-plangrid]
- Added default authenticators. [barak-plangrid]
- Dont marsh my mellow. [barak-plangrid]
- Fix the error raised by UUIDStringConverter. [Colin Hostetter]
- Add custom UUID string converter. [Colin Hostetter]
- Fix comma splice in healthcheck response message (#20) [dblackdblack]
- Start recording userId in new relic. [barak-plangrid]
- Test improvements. [Colin Hostetter]
- Fix null values in ObjectId/UUID marshmallow fields. [Colin Hostetter]
- Fix UUID field type to work with None values. [Colin Hostetter]
- Use route:method for new relic transaction name. [Colin Hostetter]
- Correctly set New Relic transaction name in restful adapter. [Colin
  Hostetter]
- Support multiple routes in RestfulApiAdapter.add_resource. [Colin
  Hostetter]
- Bump version to 1.2.0. [barak-plangrid]
- CACA-84 support capi in flask toolbox. [barak-plangrid]
- CACA-97 add scope helper functions (#13) [barak]
- Expand abbreviation. [Colin Hostetter]
- Add get_user_id_from_header_or_400 function to toolbox. [Colin
  Hostetter]
- Add docstring to QueryParamList. [Colin Hostetter]
- Add a Marshmallow list type for repeated query params. [Colin
  Hostetter]
- Version bump. [Colin Hostetter]
- Break response messages into separate file. [Colin Hostetter]
- Use keyword args for building response. [Colin Hostetter]
- Fix non-tuple returns in adapter. [Colin Hostetter]
- Use toolbox response func instead of building our own responses.
  [Colin Hostetter]
- Throw an error if an HTTP method is declared without a matching class
  method. [Colin Hostetter]
- Style changes. [Colin Hostetter]
- Use new style classes. [Colin Hostetter]
- Fix tests to work in CI. [Colin Hostetter]
- Another version bump. [Colin Hostetter]
- Add adapter to replace flask-restful Api class. [Colin Hostetter]
- Add support for exception logging via New Relic. [Colin Hostetter]
- Version bump. [Colin Hostetter]
- Only configure Bugsnag when a BUGSNAG_API_KEY is provided. [Colin
  Hostetter]

  This helps prevent spam when running automated tests, developing locally, etc.
- Add support for HTTP 422 error. [Colin Hostetter]
- Setup Jenkins (#5) [barak]

  * setup Jenkins

  * add dockerfile

  * fixup
- Increment version. [Colin Hostetter]
- Consolidate JSON loading error handling. [Colin Hostetter]
- Correctly format errors raised by request.get_json() [Colin Hostetter]
- Bump version to 1.0.0. [barak-plangrid]
- Namespace this package (#2) [barak]

  * Namespace the package

  * fixup
- Notify on 500. (#1) [Julius Alexander IV]
- Fixup. [barak-plangrid]
- Initial commit. [barak-plangrid]
