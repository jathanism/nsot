######
CentOS
######

.. note::
    This guide was written for CentOS 6.x and may be outdated. For a modern
    installation, please refer to the :doc:`ubuntu` guide or simply run
    ``pip install nsot`` on any system with Python 3.10+.

This installation guide assumes that you have installed CentOS 6.4 on your
machine, and are wanting to install NSoT. This guide will help you install NSoT
and then run it locally from a browser window.

Installation
============

To ensure your CentOS installation is up to date, please update it.
Once complete, open a command prompt and run the following:

.. code-block:: bash

    $ sudo yum install -y openssl-devel python-devel libffi-devel gcc-plugin-devel
    $ sudo yum install -y epel-release
    $ sudo yum install -y python-pip

Next you'll need to upgrade Pip to the latest version with some security addons:

.. code-block:: bash

    $ sudo pip install --upgrade pip
    $ sudo pip install requests[security]

Now we are ready to Pip install NSoT:

.. code-block:: bash

    $ sudo pip install nsot

Now you are ready to follow the :doc:`../quickstart` starting at step 2!
