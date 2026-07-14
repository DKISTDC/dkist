.. _dkist:topic-guides:vbi-stitching:

Stitching Mosaics with Reproject
================================

In this guide we cover the various options available in the reproject package for working with mosaics (mainly VBI at the time of writing).
There are many options available, which largely trade off various things against speed and memory requirements.

.. warning::

   Some of the options discussed in this page require reproject >= X.X.X


To make plots and in examples we can only use this dataset:

.. code-block:: python

	from dkist.data.sample import VBI_L1_NZJTB
