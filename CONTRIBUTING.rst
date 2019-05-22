Contributing
============

We're excited about new contributors and want to make it easy for you to help improve this project. If you run into problems, please open a GitHub issue.

If you want to contribute a fix, or a minor change that doesn't change the API, go ahead and open a pull request; see details on pull requests below.

If you're interested in making a larger change, we recommend you to open an issue for discussion first. That way we can ensure that the change is within the scope of this project before you put a lot of effort into it.

Issues
------
We use GitHub issues to track public bugs and feature requests. Please ensure your description is clear and, if reporting a bug, include sufficient instructions to be able to reproduce the issue.

Our Commitment to You
----------------------------------
Our commitment is to review new items promptly, within 3-5 business days as a general goal. Of course, this may vary with factors such as individual workloads, complexity of the issue or pull request, etc.  Issues that have been reviewed will have a "triaged" label applied by the reviewer if they are to be kept open.

If you feel that an issue or pull request may have fallen through the cracks, tag an admin in a comment to bring it to our attention. (You can start with @RookieRick, and/or look up who else has recently merged PRs).

Process
-------
Flask-Rebar is developed both internally within PlanGrid and via open-source contributions.  To coordinate and avoid duplication of effort, we use two mechanisms:

1. We use the "triaged" label to mark issues as having been reviewed.  Unless there are outstanding questions that need to be ironed out, you can assume that if an issue is marked as "triaged," we have generated an internal ticket, meaning someone will *eventually* address it.  Timing of this will largely depend on whether there's a driving need within our own codebases that relies on Flask-Rebar.
2. Because internal ticketing is a black-box to our open source contributors, we will also make use of the "assignee" feature.  If someone has picked up an internal ticket, there will be an assignee on the issue.  If you see an open issue that doesn't have an assignee and that you would like to tackle please tag a maintainer in a comment requesting assignment, and/or open an early "WIP" pull request so we'll know the issue is already being worked, and can coordinate development efforts as needed.

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

Flask-Rebar uses `semantic versions <https://semver.org/>`_. Once you know the appropriate version part to bump, use the ``bumpversion`` tool which will bump the package version, add a commit, and tag the commit appropriately.  Note, it's not a bad idea to do a manual inspection and any cleanup you deem necessary after running ``gitchangelog`` to ensure it looks good before then committing a "@cosmetic" update.

.. code-block:: bash

   git checkout -b your-release-branch
   bumpversion minor
   gitchangelog
   git commit -a -m "@cosmetic - changelog"


Then push the new commit and tags:

.. code-block:: bash

   git push -u origin your-release-branch --tags

Create a Pull Request and merge back into master.  Voila.
