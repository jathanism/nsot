###########
Quick Start
###########

Network Source of Truth is super easy to get running. If you just can't wait to
skip ahead, this guide is for you.

.. note::
    This quick start assumes a lot. If it doesn't work for you, please skip
    this and read the installation_ guide.

.. _installation: https://github.com/jathanism/nsot/blob/main/docs/installation.rst

1. Install NSoT:

   .. code-block:: bash

       $ pip install nsot

   Or using `uv <https://docs.astral.sh/uv/>`_:

   .. code-block:: bash

       $ uv pip install nsot

2. Initialize the config (this will create a default config in
   ``~/.nsot/nsot.conf.py``):

   .. code-block:: bash

       $ nsot-server init

3. Start the server on ``8990/tcp`` (the default):

   .. code-block:: bash

       $ nsot-server start

   By default, ``NSOT_NEW_USERS_AS_SUPERUSER`` is ``True``, which means any
   user authenticated via the ``X-NSoT-Email`` header is automatically created
   as a superuser. For the quick start this is convenient — no extra setup is
   needed.

   .. tip::
       If you are using session or basic authentication instead of header
       authentication, you will need to create a superuser manually:

       .. code-block:: bash

           $ nsot-server createsuperuser --email admin@localhost

       See the :ref:`configuration` docs for more details on
       ``NSOT_NEW_USERS_AS_SUPERUSER``.

4. Now fire up your browser and visit http://localhost:8990!

.. image:: _static/web_login.png
   :alt: NSoT Login

5. Log in using header authentication (the default) or the credentials created
   in step 3 if you used ``createsuperuser``.

Now, head over to the tutorial_ to start getting acquainted with NSoT!

.. _tutorial: https://github.com/jathanism/nsot/blob/main/docs/tutorial.rst
