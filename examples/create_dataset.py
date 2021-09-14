"""
Loading a Dataset
=================

This example demonstrates the `dkist.Dataset` class by loading a test dataset
from downsampled EIT images.
"""

import dkist.dataset
from dkist.data.sample import EIT_DATASET

###############################################################################
# Dataset objects are created from a directory containing one asdf file and
# many FITS files. Here we use a test dataset made from EIT images.
ds = dkist.dataset.Dataset.from_directory(EIT_DATASET)

###############################################################################
# The dataset comprises of a `dask.Array` object and a `gwcs.WCS` object. The
# array object acts like a numpy array, but loads the data from the FITS files
# on demand. Creating the dataset loads no FITS files.
print(ds)

################################################################################
# The files referenced by the dataset can be inspected by the ``.files``
# attribute. All the files are expected to be in the same directory, which is
# accessed and set by the ``.files.basepath`` attribute.
print(ds.files.basepath)

################################################################################
# The filenames are accessible via the ``.files.filenames`` attribute:
print(ds.files.filenames)

################################################################################
# It's possible to slice the dataset in the same way you would an array:
small_ds = ds[5:7, :, :]
print(small_ds)

################################################################################
# Doing this leads to referencing less files, as we have sliced along the
# dimension that is striped along the files:
print(small_ds.files.filenames)

################################################################################
# When using a non-example dataset it would be possible to transfer any missing
# files for either the whole dataset or any subset with ``.files.download``.
# Some slicing operations are not allowed on the dataset, for example strides,
# while these might be useful for only downloading some files. For this type of
# operations you can slice the files attribute directly. The following gives
# the same list of files as the array slice above.
print(ds.files[5:7].filenames)
