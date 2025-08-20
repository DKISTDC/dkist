(dkist:tutorial:index)=
# Python Tools Tutorial

Welcome to the DKIST tutorial.
In this tutorial we shall guide you through getting started with DKIST data.
By the end of this tutorial you should be familiar with how to:

* Search for level one datasets using `Fido`.
* Loading these datasets with `dkist.load_dataset`.
* Inspecting the `dkist.Dataset` object and how to work with it.
* How to transfer FITS files to your local computer using Globus.
* How to do some basic plotting of the DKIST data.

Before you get started with this tutorial follow {ref}`dkist:installation` to get Python and the ``dkist`` package installed.

```{note}
If you want to follow this tutorial interactively, you have two options.

The easiest is to use an online service to run notebooks called [Binder ![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/DKISTDC/DKIST-Workshop/stable?urlpath=%2Ftree%2Findex.ipynb).
The downside of this is that you can't use Globus to download files and some more complex visualization examples fail because of memory limitations.

Alternatively we have instructions for running the tutorial as Jupyter Notebooks locally: {ref}`dkist:workshop_install`
```


**Contents**

```{toctree}
:maxdepth: 1
1_astropy_and_sunpy
2_search_and_asdf_download
3_dataset_dimensionality
4_dataset_files
5_tileddataset
6_downloading_data
7_visualization
```
