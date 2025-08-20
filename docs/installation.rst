.. _dkist:installation:

Installation and Setup
======================

Python
------

If you don't already have a Python installation then we recommend installing Python with `miniforge <https://github.com/conda-forge/miniforge/#miniforge>`__.
If you already have Python and either ``conda`` or ``pip`` working you can skip the next section.

Installing miniforge
~~~~~~~~~~~~~~~~~~~~

First, download the installer for your system and architecture from the links below:

.. grid:: 3

    .. grid-item-card:: :fab:`linux` Linux

        `x86-64 <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh>`__

        `aarch64 <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh>`__

    .. grid-item-card:: :fab:`windows` Windows
        :link: https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe

        `x86-64 <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe>`__

    .. grid-item-card:: :fab:`apple` Mac

        `arm64 (Apple Silicon) <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Darwin-arm64.sh>`__

        `x86-64 <https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Darwin-x86_64.sh>`__

.. note::

    See the `Miniforge <https://github.com/conda-forge/miniforge>`__ page for more details and architectures.

Then select your platform to install miniforge:

.. tab-set::

    .. tab-item:: :fab:`linux` :fab:`apple` Linux & Mac
        :sync: platform

        Linux & Mac Run the script downloaded above, with
        ``bash <filename>``. The following should work:

        .. code-block:: console

           bash Miniforge3-$(uname)-$(uname -m).sh

        Once the installer has completed, close and reopen your terminal.

    .. tab-item:: :fab:`windows` Windows
        :sync: platform

        Double click the executable file downloaded from
        the links above.

        Once the installer has completed you should have a new "miniforge
        Prompt" entry in your start menu.


In a new terminal (miniforge Prompt on Windows) run ``conda list`` to test that the install has worked.

Installing ``dkist`` with conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow this section if you have just installed miniforge, or if you have conda installed from miniconda or anaconda.

Open a new terminal (miniforge Prompt or anaconda prompt on Windows) and run:

.. code-block:: bash

    conda create -n dkist
    conda activate dkist

to create a new environment for this workshop, and then activate it. Then run:

.. code-block:: bash

    conda install -c conda-forge dkist

Installing ``dkist`` with pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you know what you are doing and have Python installed without conda, please make a clean virtual environment and run:

.. code-block:: bash

    pip install dkist


.. _dkist:installation:globus:

Globus
------

To download DKIST science data you need `Globus Connect Personal (GCP) <https://www.globus.org/globus-connect-personal>`__, and a Globus account.
The `DKIST Help Desk <https://nso.atlassian.net/servicedesk/customer/portal/3/article/247694160>`__ has some pages to help with this.
However, this is not necessary for downloading ASDF metadata files, which can be done using the SunPy Fido client.
See :ref:`dkist:topic-guides:searchdownload` for more detail on this distinction.
