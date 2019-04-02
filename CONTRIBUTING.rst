Contributing
============

We're excited about new contributors and want to make it easy for you to help improve this project. If you run into problems, please open a GitHub issue.

If you want to contribute a fix, or a minor change that doesn't change the API, go ahead and open a pull requests, see details on pull requests below.

If you're interested in making a larger change, we recommend you to open an issue for discussion first. That way we can ensure that the change is within the scope of this project before you put a lot of effort into it.

Our Commitment to You
----------------------------------

Our commitment is to review new items promptly, within 3-5 business days as a general goal. Of course, this may vary with factors such as individual workloads, complexity of the issue or pull request, etc.  After review, any open Issue should always have an assignee.

If you feel that an Issue or Pull Request may have fallen through the cracks, tag an admin in a comment to bring it to our attention. (You can start with @RookieRick, and/or look up who else has recently merged PRs).

Issues
------

We use GitHub issues to track public bugs. Please ensure your description is clear and has sufficient instructions to be able to reproduce the issue.


Developing
----------

We recommend using a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ for development. Once within a virtual environment install the ``flask_rebar`` package:

.. code-block:: bash

   pip install -r requirements.txt

We use `black` to format code and keep it all consistent within the repo. With that in mind, you'll also want to install the precommit hooks because your build will fail if your code isn't black:

.. code-block:: bash

   pre-commit install

To run the test suite with the current version of Python/virtual environment, use pytest:

.. code-block:: bash

   pytest

Flask-Rebar supports multiple versions of Python, Flask, and Marshmallow and uses Travis CI to run the test suite with different combinations of dependency versions. These tests are required before a PR is merged.


Pull Requests
-------------

1. Fork the repo and create your branch from ``master``.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Make sure you commit message matches something like `(chg|fix|new): COMMIT_MSG` so `gitchangelog` can correctly generate the entry for your commit.


Releasing to PyPI
-----------------

Travis CI handles releasing package versions to PyPI.

Flask-Rebar uses `semantic versions <https://semver.org/>`_. Once you know the appropriate version part to bump, use the ``bumpversion`` tool to bump the package version, add a commit, and tag the commit appropriately:

.. code-block:: bash

   git checkout master
   gitchangelog
   bumpversion minor

Then push the new commit and tags to master:

.. code-block:: bash

   git push origin master --tags

Voila.
