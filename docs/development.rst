Development
===========

Git Branches
------------

The primary branch for NSoT development is ``main``. All Pull Requests should
be opened against ``main``.

Releases are managed automatically via `python-semantic-release
<https://python-semantic-release.readthedocs.io>`_ and GitHub Actions. See
:ref:`release-process` for more information.

Setting up Your Environment
---------------------------

We use `uv <https://docs.astral.sh/uv/>`_ for dependency management. To get
started, install uv and then clone the repository:

.. code-block:: bash

    $ git clone git@github.com:jathanism/nsot.git
    $ cd nsot
    $ uv sync --all-extras

This installs all runtime, dev, and docs dependencies into a managed virtual
environment.

Running a Test Instance
-----------------------

For developement and testing, it's easiest to run NSoT behind a reverse proxy
that handles authentication and sends a username via a :ref:`special HTTP
header <api-auth_header>`. We've included a test proxy for running on
development instances.

To get started, follow these steps:

.. code-block:: bash

    # Initialize the config
    $ nsot-server init

    # Setup the database.
    $ nsot-server upgrade

    # Run the development reverse proxy (where $USER is the desired username)
    $ nsot-server user_proxy $USER

    # (In another terminal) Run the front-end server
    $ nsot-server start

**Note:** This quick start assumes that you're installing and running NSoT on
your local system (aka `localhost`).

Now, point your web browser to http://localhost:8991 and explore the
`documentation <https://nsot.readthedocs.io>`_!

Running Unit Tests
------------------

All tests will automatically be run on GitHub Actions when pull requests are
sent. However, it's beneficial to run the tests often during development:

.. code-block:: bash

    $ NSOT_API_VERSION=1.0 uv run pytest -vv tests/

Working with Database Migrations
--------------------------------

If you make any changes to the database models you'll need to generate a new
migration. We use Django's built-in support for database migrations underneath,
so for general schema changes is should be sufficient to just run:

.. code-block:: bash

    $ nsot-server makemigrations

This will generate a new schema version. You can then sync to the latest
version:

.. code-block:: bash

    $ nsot-server migrate

Working with Docs
-----------------

Documentation is generated using `Sphinx <http://sphinx-doc.org/>`_. If you
just want to build and view the docs | you cd into the ``docs`` directory and
run ``make html``. Then point your browser | to
``docs/\_build/html/index.html`` on your local filesystem.

If you're actively modifying the docs it's useful to run the autobuild server:

.. code-block:: bash

    $ uv run sphinx-autobuild docs docs/_build/html/

This will start a server listening on a port that you can browse to and will be
automatically reloaded when you change any rst files. One downside of this
approach is that is doesn't refresh when docstrings are modified.

Front-end Development
---------------------

We use a combination JavaScript utilities to do front-end development:

+ `npm <https://www.npmjs.com/>`_ - npm is used to manage our build dependencies
+ `gulp <http://gulpjs.com/>`_ - gulp for building, linting, testing

Adding New Build Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the most part you shouldn't need to care about these details though if you
want to add new build dependencies, for example `gulp-concat
<https://github.com/contra/gulp-concat>`_, you would run the following:

.. code-block:: bash

    # Install gulp-concat, updating package.json with a new devDependency
    $ npm install gulp-concat --save-dev

    # Writes out npm-shrinkwrap.json, including dev dependencies, so consistent
    # build tools are used
    $ npm shrinkwrap --dev

Adding New Web Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Install lodash, updating package.json with a new dependency
    $ npm install lodash --save
    $ npm shrinkwrap --dev
    # Update VENDOR_FILES in gulpfile.js with the source files to include

We explicitly include minified versions of web dependencies, so after
updating ``package.json`` with the new package you need to update the
VENDOR_FILES variable in ``gulpfile.js`` to let the build workflow know
which files to include.

Linting and Formatting
----------------------

We use `ruff <https://docs.astral.sh/ruff/>`_ for linting and code formatting:

.. code-block:: bash

    # Check for lint issues
    $ uv run ruff check nsot/ tests/

    # Auto-format code
    $ uv run ruff format nsot/ tests/

.. _versioning:

Versioning
----------

We use `semantic versioning <http://semver.org>`_. Version numbers will
follow this format::

    {Major version}.{Minor version}.{Revision number}

Patch version numbers (0.0.x) are used for changes that are API compatible. You
should be able to upgrade between minor point releases without any other code
changes.

Minor version numbers (0.x.0) may include API changes, in line with the
:ref:`deprecation-policy`. You should read the release notes carefully before
upgrading between minor point releases.

Major version numbers (x.0.0) are reserved for substantial project milestones.

.. _release-process:

Release Process
---------------

Releases are automated via `python-semantic-release
<https://python-semantic-release.readthedocs.io>`_ and GitHub Actions. When
commits following the `Conventional Commits
<https://www.conventionalcommits.org/>`_ format are merged to ``main``,
semantic-release determines the next version, updates the changelog, tags the
release, and publishes to PyPI.

Commit prefixes that trigger releases:

- ``fix:`` — patch release
- ``feat:`` — minor release
- ``BREAKING CHANGE:`` — major release

Other prefixes (``docs:``, ``ci:``, ``chore:``, ``refactor:``, ``test:``) do
**not** trigger a release.

To build the package locally:

.. code-block:: bash

    $ uv build

.. _deprecation-policy:

Deprecation policy
------------------

NSoT releases follow a formal deprecation policy, which is in line with
`Django's deprecation policy <https://docs.djangoproject.com/en/stable/internals/release-process/#internal-release-deprecation-policy>`_.

The timeline for deprecation of a feature present in version 1.0 would work as follows:

* Version 1.1 would remain **fully backwards compatible** with 1.0, but would raise
  Python ``PendingDeprecationWarning`` warnings if you use the feature that are
  due to be deprecated. These warnings are **silent by default**, but can be
  explicitly enabled when you're ready to start migrating any required changes.

  Additionally, a ``WARN`` message will be logged to standard out from the
  ``nsot-server`` process.

  Finally, a ``Warning`` header will be sent back in any response from the API.
  For example::

    Warning: 299 - "The `descendents` API endpoint is pending deprecation. Use
    the `descendants` API endpoint instead."

* Version 1.2 would escalate the Python warnings to ``DeprecationWarning``,
  which is **loud by default**.
* Version 1.3 would remove the deprecated bits of API entirely and accessing
  any deprecated API endoints will result in a ``404`` error.

Note that in line with Django's policy, any parts of the framework not
mentioned in the documentation should generally be considered private API, and
may be subject to change.
