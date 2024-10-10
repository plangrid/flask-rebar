Changelog
=========


v3.3.2 (2024-10-10)
-------------------

Fix
~~~
- Make `raise_400_for_marshmallow_errors` raise again (#317) [Greg
  Kuwaye]

  Buried in #300 was a consequential change to `raise_400_for_marshmallow_errors`
  that changed its behavior from raising errors to returning them.

  This affects >= 3.2.0.

  This PR reverts this behavior since there seems to be no need for this change.

Other
~~~~~
- [PJL-10221] handle some edge cases in OpenAPI v3.1 swagger generation
  (#319) [Eugene Kim]

  * Bugfix for ContainsOnly marshmallow validator
  * Fix to allow custom dict attributes to be typed


- Merge pull request #318 from plangrid/ACSBP-4867. [Zuhair Taleb]

  Add stalebot to flask-rebar [ACSBP-4867]
- Add stalebot to flask-rebar [ACSBP-4867] [Zuhair Taleb]


v3.3.1 (2024-08-08)
-------------------

Fix
~~~
- Handle `type` when it is a list. [Greg Kuwaye]

Other
~~~~~
- Merge pull request #315 from kaiku/gkuwaye/issue-314-repro. [Greg
  Kuwaye]

  Fix schema flattener to support list-type `type` field introduced in OpenAPI 3.1
- Update flask_rebar/swagger_generation/generator_utils.py. [Daniel
  Wallace, Greg Kuwaye]
- Revert "Add failing test to repro issue#314" [Greg Kuwaye]

  This reverts commit f2546ee3d02964b5e516f0c2c34c1756ea823f43.
- Add failing test to repro issue#314. [Greg Kuwaye]


v3.3.0 (2024-04-15)
-------------------
- Merge pull request #313 from plangrid/release_4-15-24/3.3.0. [Scott
  Josephson]

  Bump version: 3.2.1 → 3.3.0
- Merge pull request #311 from plangrid/jonls/async-handler. [Jon Lund
  Steffensen]

  Async handler support
- Async handler support. [Jon Lund Steffensen]


v3.2.1 (2024-03-27)
-------------------

Changes
~~~~~~~
- Provide clear vulnerability reporting instructions. [Nicholas
  Lawrence]
- Provide clear vulnerability reporting instructions. [Nicholas
  Lawrence]

Fix
~~~
- Remove packaging dependency for checking version. [Verina Georgy]
- Update depreciated marshmallow version check. [Verina Georgy]

Other
~~~~~
- Bump Version: 3.2.0 → 3.2.1 (#309) [Verina Georgy]

  Bump version: 3.2.0 → 3.2.1
- Merge pull request #308 from plangrid/update-pypa/gh-action-pypi-
  release-tag. [Verina Georgy]

  build: update pypa/gh-action-pypi-publish tag to release/v1
- Merge branch 'master' into update-pypa/gh-action-pypi-release-tag.
  [Verina Georgy]
- Merge pull request #306 from vkunz/runtime-deps. [Nicholas Lawrence]

  add missing runtime dependencies
- Merge branch 'master' into runtime-deps. [Nicholas Lawrence]
- Update why.rst. [David Hariri]

  Just was reading the docs and found a few typos.
- Merge branch 'master' into runtime-deps. [Verina Georgy]
- Merge pull request #307 from plangrid/ACSBP-4569-resolve-marshmallow-
  depreciation-errors. [Verina Georgy]

  [ACSBP-4569] Fix Test Failures Due to Marshmallow Depreciation Warnings
- Setuptools: add Werkzeug as a runtime dependency. [Valentin Kunz]

  Bits from this module are used directly within flask-rebar.
- Setuptools: demote typing-extensions dependency. [Valentin Kunz]

  Polyfills within typing-extensions dependency are only used within
  specific python versions.

  Limit the dependency to those specific versions.
- Types: limit polyfill usage to unsupported python versions. [Valentin
  Kunz]

  Type class ParamSpec was made available with python3.10.

  Limit polyfill import to python versions missing ParamSpec.
- Setuptools: pull in typing-extensions as a runtime depndency.
  [Valentin Kunz]

  Flask-rebar uses type classes not available in all supported python
  versions.

  Missing type classes are imported from typing-extensions.
- Build: update pypa/gh-action-pypi-publish tag to release/v1. [Verina
  Georgy]


v3.2.0 (2024-02-16)
-------------------
- Merge pull request #303 from plangrid/sj/release-2-16-2024. [Scott
  Josephson]

  Bump version: 3.1.1 → 3.2.0
- Add mypy type hints to all non-test code + update mypy config (#300)
  [Eugene Kim]

  * begin adding type hints

  * fixes

  * more hints

  * 1

  * 1

  * 1

  * type hint marshmallow converters

  * 1

  * revert

  * change import to hopefully make compatible with older python

  * more fixes for old python

  * fix for old marshmallow

  * generator v2

  * v3 generator

  * swagger objects

  * more typing

  * add a few missing hints

  * add typed

  * minor fixes

  * update type + rerun black

  * more type hints

  * finish adding type hints

  * fix tests

  * address comments

  * fix

  * minor fix

  * fix typo


v3.1.1 (2023-10-27)
-------------------
- Dont test python 3.12 right now. [Daniel Wallace]
- Bump flask dependency to include 3.0. [Daniel Wallace]


v3.1.0 (2023-10-26)
-------------------

Fix
~~~
- Prevent hidden methods from being included in schema (#298) [Daniel
  Wallace, mbierma, mbierma]

  * Prevent hidden methods from being included in schema

  * Fixup processing for including hidden entries

  * Add tests

  * blacken

  ---------

Other
~~~~~
- Linting. [Daniel Wallace]
- Missed one. [Daniel Wallace]
- Use EnumField from marshmallow to swagger. [Daniel Wallace]
- Update documentation. [Daniel Wallace]
- Add example to todo app. [Daniel Wallace]
- Change the logic around. [Daniel Wallace]
- Blacken. [Daniel Wallace]
- Allow specifying swagger documents for path converters. [Daniel
  Wallace]

  without much changing elsewhere, this allows us to set enum types for
  custom path converters in flask.

  for example: `/v1/preferences/<preference_type:scope>` where scope could
  be `user`, `project`, or `account`. We can define an object with a
  `to_swagger` function as part of the [Flask
  Converter](https://flask.palletsprojects.com/en/2.3.x/api/#flask.Flask.url_map)
  that is defined.
- Blacken. [mbierma]
- Support optional short summary for paths. [mbierma]


v3.0.0 (2023-08-08)
-------------------
- Merge pull request #294 from plangrid/acsbp-more-syntax-fixes. [Scott
  Josephson]

  Acsbp - more syntax fixes
- Add rst linter to precommit. [Scott Josephson]
- Fix syntax. [Scott Josephson]
- Merge pull request #293 from plangrid/acsbp/sj-fix-syntax-in-readme.
  [Scott Josephson]

  fix syntax in readme
- Fix syntax. [Scott Josephson]
- Install mypy + update dev deps + update pre commit + begin type
  hinting (#292) [Eugene Kim]

  * update all dev dependencies to latest version

  * install mypy, update pre commit, fix minimal required type hints

  * fix tests

  * fix python 3.8

  * trailing line breaks

  * another 3.8 fix

  * run pyupgrade to python 3.8

  * trailing empty line

  * comment

  * move to pyproject
- Merge pull request #284 from plangrid/acsbp-3718. [Scott Josephson]

  ACSBP-3718 Update to use openapi 3.1
- Remove B950 update. [Scott Josephson]
- Lint: blackify. [Scott Josephson]
- Update jsonschema. [Scott Josephson]
- Revert "set id to schema url as per" [Scott Josephson]

  This reverts commit 8474029d8b5470baa524f786101d4ad6ebdc2d19.
- Set id to schema url as per https://json-
  schema.org/specification.html#output-schemas-and-examples. [Scott
  Josephson]
- Update true -> True. [Scott Josephson]
- Replace false -> False. [Scott Josephson]
- Update OApi 3.1 spec. [Scott Josephson]
- Fix version. [Scott Josephson]
- Update static files. [Scott Josephson]
- Merge branch 'master' into acsbp-3718. [Scott Josephson]
- Readme: add shell command for replacing ui files. [Scott Josephson]
- Swagger: update static dir with latest dist files. [Scott Josephson]
- Merge branch 'master' into acsbp-3718. [Scott Josephson]
- Fix linting with black. [Scott Josephson]
- Updates for 3.1. [Scott Josephson]
- Merge branch 'master' into acsbp-3718. [Scott Josephson]
- Convert to using null as a type. [Scott Josephson]
- Black created some line length problems for flake8 see: https://black.
  readthedocs.io/en/stable/the_black_code_style/current_style.html#line-
  length. [Scott Josephson]
- Black reformat. [Scott Josephson]
- Uppercase booleans. [Scott Josephson]
- Update json-schema for v3. [Scott Josephson]
- Change references from 3.0.2 --> 3.1.0. [Scott Josephson]
- Updated v3 version. [Scott Josephson]
- Update comment. [Scott Josephson]
- Use 3.1.0. [Scott Josephson]


v2.4.1 (2023-06-30)
-------------------

Changes
~~~~~~~
- Update deprecated Marshmallow calls [Andrew Standley]


v2.4.0 (2023-05-16)
-------------------

Changes
~~~~~~~
- Update to use Enum in 3.18.0. [Daniel Wallace]

  Enum is basically a drop in replacement for EnumField from
  marshmallow_enum. But it does not have the same load_by or dump_by
  options.

Fix
~~~
- Resolve a minor bug in swagger v3 generator [PJL-7600] [Eugene Kim]


v2.3.0 (2022-11-29)
-------------------

New
~~~
- Add the ability to auto import handlers. [Daniel Wallace]

  Users can now configure Rebar to import all modules in a directory
  to load all registered handlers. This avoids tedium where previously
  users had to explicitly import modules so that their handlers were
  registered with the Rebar registry.

Fix
~~~
- Remove periods from blueprint name prefixes. [Rishi Mukhopadhyay]

- Registry.handlers should always be a list. [Daniel Wallace]

Other
~~~~~
- Use flask standards for files. [Daniel Wallace]
- Python 3.11 support. [Daniel Wallace]
- Remove a deprecated version check (#276) [Eugene Kim]


v2.2.1 (2022-06-03)
-------------------

Fix
~~~
- Try to fix dumping with data_key. [Jon Lund Steffensen]


v2.2.0 (2022-03-31)
-------------------
- Unbreak with werkzeug 2.1 (#268) [Rick Riensche]

  * Remove deprecated safe_str_cmp and remove werkzeug pin

  * Update black

  * Update CI test coverage for Flask+werkzeug 2.1


v2.1.2 (2022-03-31)
-------------------
- Pin werkzeug to avoid breaking change (#266) [Rick Riensche]
- Don't block CI based on old versions of Flask/werkzeug or EOL Python versions
- Use unittest.mock instead of mock. [Rick Riensche]
- Update pytest for pytest-order support. [Rick Riensche]
- Add pytest-order to dev extras. [Rick Riensche]
- Only use EnumConverter if marshmallow-enum present. [Rick Riensche]
- Add marshmallow-enum convertor to flask-rebar. [Daniel Wallace]


v2.1.1 (2022-01-10)
-------------------

Fix
~~~

- Fix filter_dump_only for NoneType nested fields (#262) [mbierma]


v2.1.0 (2021-10-19)
-------------------

Fix
~~~

Add Python 3.10 support:

- Use Mapping from abstract classes (#259) [Daniel Wallace]

  * Mapping was removed from collections in 3.10 and is only available in collections.abc now.

  * update pytest for py3.10 support

  * add py3.10 to pr workflow

  * use setupactions v2



v2.0.2 (2021-08-09)
-------------------

Fix
~~~

- Bumpversion bumped mock :( [Rick Riensche]


v2.0.1 (2021-08-09)
-------------------

Fix
~~~
- Remove now-pointless (and worse, broken) DisallowExtraFieldsMixin
  (#253) [Rick Riensche]
- Handle dump_only fields properly (#251) [Rick Riensche]


v2.0.0 (2021-07-27)
-------------------

Changes
~~~~~~~
- Add internal error codes  (#245) [Rick Riensche]

  * add error codes to ride alongside human-readable messages

  * Allow rename or suppression of flask_error_code in error responses
- Rename swagger_path to spec_path (#214) [Matthew Janes, Rick Riensche]

  * https://github.com/plangrid/flask-rebar/issues/98

  * Continuation of work started here: https://github.com/plangrid/flask-rebar/pull/209

  * Use deprecation util to make this more forgiving

- Remove previously deprecated things that have passed EOL (#246) [Rick
  Riensche]

  * remove deprecated 'marshal_schema' alias for 'response_body_schema'

  * remove deprecated (and already broken) converters parameter to ``AuthenticatorConverterRegistry``

- Add support for marshmallow-objects (#243) [Rick Riensche]

- Add support for flask 2.0 (#239) [Eugene Kim]

- Store "rebar" in app.extensions on rebar.init_app (#230) [twosigmajab]

  *  Include handler_registries so that it's possible to enumerate all the Rebar APIs a Flask app provides given only a reference to the app object.


Fix
~~~
- Update list of versions for automated tests + fix broken test (#238)
  [Eugene Kim]

- Remove deprecated method and update docs (#216) [Rick Riensche]

  * fix: remove deprecated authenticator converter methods and update docs

- Issue 90: Fix for self-referential nested fields (#226) [Pratik
  Pramanik, Rick Riensche]

- Fix bug that prevents returning `Flask.Response`s. (#153)
  [twosigmajab]

Other
~~~~~

- Remove unused imports via Deepsource (#222) [Matthew Janes,
  deepsource-autofix[bot]]


- Remove old ref to TravisCI. [Rick Riensche]

- Drop Python 3.5 (fixes #220) (#221) [twosigmajab]
- Bump version to RC2. [Brock Haywood]
- Dropping Marshallow_v2 support (#195) [Ali Scott, Matthew Janes, Rick
  Riensche]


- Enabling hidden APIs in flask-rebar  (#191) [Ali Scott]


- Rename create_handler_registry's "swagger_path" param (#209) [Ali
  Scott]


- Removing Actually from class names (#207) [Ali Scott]

- Fix trigger for auto-release on tag (#203) [Rick Riensche]
- Remove pyyaml pin since it is not needed anymore (#192) [Daniel
  Wallace]

  * We have dropped support for python3.4, which is why pyyaml was pinned.
- Doc: Fix code typos in recipes examples (#190) [Krismix1]
- Fix minor typos in swagger_generation.rst (#188) [Matthew Janes]


v1.12.2 (2020-08-04)
--------------------
- Change trigger. [Rick Riensche]

  Auto-release on tag beginning with "v"
- Troubleshooting build-and-publish. [Rick Riensche]

  Add explicit mention of ref to checkout per https://github.com/actions/checkout/issues/20#issuecomment-524521113 (from the comment that follows this one though I'm not sure why this didn't work before if this DOES fix it.. :P )
- Authenticator_converter_registry is missing register_type. [Brock
  Haywood]
- Doc: Add meeting notes from Jan 29 Roadmap Call (#165) [Rick Riensche]
- Fix name and tweak "types" [Rick Riensche]

  More closely align with what is included if you use GitHub's built-in package example (in attempt to make this actually trigger which it doesn't seem to have done when I created 1.12.1)


v1.12.1 (2020-03-26)
--------------------
- Fixes for oneof on _flatten (#182) [Francisco Castro]
- Add github actions to workflow (#177) [Daniel Wallace]

  * add workflows for github actions
  + removed python3.4 because it is end of lifed and doesn't exist on
  github.
  + removed marshmallow 3.0.0rc5 since newer 3 versions have changed
  the api.  Also, marshmallow 3.0 seems to have dropped support for
  python2.
  + remove .travis.yml
- !chg: Remove Flask-Testing dependency and drop Python 3.4 support.
  (#173) [Andrew Standley]

  * Remove Flask-Testing dependency.
  * Added JsonResponseMixin from Flask-Testing which we need as long as we continue to test flask<1.0
  * Pinned Werkzueg in travis. Should be able to drop if we drop flask<0.12 support.
  * Dropped support for python 3.4 in order to test support for Werkzeug 1.0.0
- FIX: Fix OpenApi v3 generation for nullable fields (#154) [mbierma]

  * Use 'nullable' to specify that the value may be null when generating v3 schema.
- Change host default to localhost (#157) [Daniel Wallace]


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
