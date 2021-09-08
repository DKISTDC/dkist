.. _install:

Installation
============

To get started you should follow the `sunpy installation guide <https://docs.sunpy.org/en/stable/guide/installation.html>`__ as a working sunpy installation is a prerequisite for using the DKIST tools.

Once you have a working sunpy installation you should run::

  $ pip install dkist[all]

to install the DKIST tools.

.. note::

   Conda packages will be made available after the first official release of the package.


Build from Source
-----------------

If you wish to install the development version of the `dkist` package you can clone the git repository::

  $ git clone https://github.com/DKISTDC/dkist

and then install the package in "editable" mode which symlinks the repository into your Python path::

  $ pip install --editable ".[tests,docs]"
