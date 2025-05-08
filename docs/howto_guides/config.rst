.. _dkist:topic-guides:config:

Configure the `dkist` package
=============================

There are a few parts of the `dkist` package which can be configured.
The `dkist` configuration system makes use of the ``astropy`` config system, which you can read about here: :ref:`astropy_config`.

Currently the `dkist` package provides config options as does the `dkist.net` subpackage.


At runtime
----------

The configuration system provides a Python API to change config values at runtime.
For example to change the port used for the Globus authentication callback you can do this:

.. code-block:: python

    >>> from dkist.net import conf
    >>> conf.globus_auth_port = 8112

Other configuration options are documented below.


With a file
-----------

To persist your configuration changes you can write a configuration file.
The easiest way to do this is to create a default config file using the `dkist.write_default_config` function:

.. code-block:: python

    >>> import dkist
    >>> dkist.write_default_config()
    INFO: The configuration file has been successfully written to ...dkist.cfg [astropy.config.configuration]
    True

This should print out the location where the file was written, then you can edit this file with the values of your configuration options.


Available Configuration Options
-------------------------------

.. note::

   The lower case ``conf`` should be used, not the ``Conf`` class, when setting options from Python.


.. autoclass:: dkist::Conf
   :members:
   :undoc-members:


.. autoclass:: dkist.net::Conf
   :members:
   :undoc-members:
