Contributing
============

We're excited about new contributors and want to make it easy for you to help improve this project. If you run into problems, please open a GitHub issue.

If you want to contribute a fix, or a minor change that doesn't change the API, go ahead and open a pull requests, see details on pull requests below.

If you're interested in making a larger change, we recommend you to open an issue for discussion first. That way we can ensure that the change is within the scope of this project before you put a lot of effort into it.


Issues
------

We use GitHub issues to track public bugs. Please ensure your description is clear and has sufficient instructions to be able to reproduce the issue.


Developing
----------

We recommend using a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ for development. Once within a virtual environment install the ``flask_rebar`` package:

.. code-block:: bash

   pip install -r requirements.txt

To run the test suite with the current version of Python/virtual environment, use pytest:

.. code-block:: bash

   pytest

Flask-Rebar supports multiple versions of Python, Flask, and Marshmallow and uses Travis CI to run the test suite with different combinations of dependency versions. These tests are required before a PR is merged.


Pull Requests
-------------

1. Fork the repo and create your branch from ``master``.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Add an entry to the ``CHANGELOG.md`` for any breaking changes, enhancements, or bug fixes.


Releasing to PyPI
-----------------

Travis CI handles releasing package versions to PyPI.

Flask-Rebar uses `semantic versions <https://semver.org/>`_. Once you know the appropriate version part to bump, use the ``bumpversion`` tool to bump the package version, add a commit, and tag the commit appropriately:

.. code-block:: bash

   git checkout master
   bumpversion minor

Then push the new commit and tags to master:

.. code-block:: bash

   git push origin master --tags

Voila.
