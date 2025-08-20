:orphan:

.. _dkist:workshop_install:

Instructions for Running Tutorial Notebooks
===========================================

If you are attending the DKIST workshop or if you want to run the tutorial notebooks locally then these instructions will guide you in downloading the notebooks and installing the extra requirements.

Don't forget to also install and configure :ref:`dkist:installation:globus`.


Installing Notebook Requirements
--------------------------------

Before following this page you **must** follow the steps in :ref:`dkist:installation`, by the end of these instructions you should have an environment named "dkist".

First activate the dkist environment:

.. code-block:: bash

    conda activate dkist

Then we need to install the dependencies for running the notebooks locally:

.. code-block:: bash

    conda install -c conda-forge notebook jupyterlab-myst ipympl ipywidgets distributed

If you don't already have git installed also run:

.. code-block:: bash

    conda install -c conda-forge git


Downloading the Notebooks
-------------------------

The best way to download the notebooks is with git, as this will let you update them.
Run the following command in a directory where you want to store the notebooks, it will create a directory named ``DKIST-Workshop``.

.. code-block:: bash

	git clone https://github.com/DKISTDC/DKIST-Workshop.git

If this doesn't work you can also download a zip file of the notebooks `here <https://github.com/DKISTDC/DKIST-Workshop/archive/refs/heads/stable.zip>`__.

Then change into this directory and run jupyter:

.. code-block:: bash

	cd DKIST-Workshop
	jupyter notebook


The notebooks in the ``instructor`` folder have the code cells pre-filled, the others are blank to allow you to fill in the content from the :ref:`dkist:tutorial:index`.
